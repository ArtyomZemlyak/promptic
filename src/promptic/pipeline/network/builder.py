"""Node network builder for constructing recursive node networks."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from promptic.context.nodes.errors import (
    NodeNetworkDepthExceededError,
    NodeNetworkValidationError,
    NodeReferenceNotFoundError,
    NodeResourceLimitExceededError,
    PathResolutionError,
)
from promptic.context.nodes.models import ContextNode, NetworkConfig, NodeNetwork
from promptic.format_parsers.registry import get_default_registry
from promptic.resolvers.base import NodeReferenceResolver
from promptic.resolvers.filesystem import FilesystemReferenceResolver
from promptic.versioning import VersionSpec

# AICODE-NOTE: Token counting removed - not used in examples 003-006.
# Removed import: from promptic.token_counting.base import TokenCounter


class NodeNetworkBuilder:
    """Orchestrates loading multiple nodes, resolving references, and constructing the network graph.

    # AICODE-NOTE: This class implements network building with cycle detection using DFS algorithm.
    The algorithm maintains a visited set and recursion stack to detect cycles efficiently.
    Depth limits are enforced during traversal to prevent stack overflow from extremely deep trees.
    Reference validation ensures all references resolve to existing nodes before network construction.
    """

    def __init__(
        self,
        resolver: NodeReferenceResolver | None = None,
    ):
        """Initialize network builder with optional resolver.

        # AICODE-NOTE: Token counting removed - not used in examples 003-006.
        # Removed parameter: token_counter. Network building now focuses on
        # structure validation (cycles, depth, size) without token tracking.

        The builder uses dependency injection for resolver to enable
        testing and custom resolution strategies. If not provided, defaults are used.

        Side Effects:
            - Creates default FilesystemReferenceResolver if resolver is None
            - No external state mutation

        Args:
            resolver: Reference resolver for resolving node references. Must implement
                NodeReferenceResolver interface. Defaults to FilesystemReferenceResolver
                which resolves file paths relative to base directories.

        Example:
            >>> from promptic.resolvers.filesystem import FilesystemReferenceResolver
            >>> resolver = FilesystemReferenceResolver()
            >>> builder = NodeNetworkBuilder(resolver=resolver)
        """
        self.resolver = resolver or FilesystemReferenceResolver()

    def build_network(
        self,
        root_path: Path,
        config: NetworkConfig | None = None,
        version: Optional[VersionSpec] = None,
    ) -> NodeNetwork:
        """Build a node network from a root path with recursive reference resolution.

        # AICODE-NOTE: Token counting removed - not used in examples 003-006.
        # Network metrics now track only size and depth, not tokens.

        This method orchestrates the complete network building process:
        1. Loads the root node using format detection (with version resolution if version provided)
        2. Recursively resolves all references using the configured resolver (with version resolution)
        3. Validates network structure (cycles, depth, resource limits)
        4. Calculates network metrics (size, depth)
        5. Returns a complete NodeNetwork instance

        # AICODE-NOTE: Version-aware network building: When version is provided, the builder
        uses version-aware path resolution for both the root node and all referenced nodes.
        This enables hierarchical versioning where different parts of a prompt hierarchy
        can use different versions. Version resolution is applied at the path resolution
        level, so it works transparently with the existing resolver architecture.

        Side Effects:
            - Reads multiple files from filesystem (recursive loading)
            - Uses format parser registry for each node
            - Mutates node.children lists (adds resolved child nodes)
            - No external state mutation (pure except for I/O and node mutation)

        Args:
            root_path: Path to root node file (relative or absolute). The path
                is used to determine the base directory for resolving relative references.
                If root_path is a directory and version is provided, version resolution
                is applied to select the appropriate versioned file.
            config: Network configuration with limits. Defaults to
                NetworkConfig() with standard limits (max_depth=10, max_node_size=10MB,
                max_network_size=1000).
            version: Optional version specification for version-aware resolution ("latest",
                "v1", "v1.1", "v1.1.1", or hierarchical dict). If provided, version
                resolution is applied to both root path and all referenced paths.

        Returns:
            NodeNetwork instance with:
            - All nodes loaded and references resolved
            - Network validated (no cycles, within limits)
            - Metadata calculated (total_size, depth)
            - Root node with children populated

        Raises:
            NodeNetworkValidationError: If cycle detected during traversal. Error
                includes cycle path details for debugging.
            NodeNetworkDepthExceededError: If network depth exceeds config.max_depth.
                Includes current depth and limit in error message.
            NodeReferenceNotFoundError: If any reference cannot be resolved by the
                resolver. Includes reference path and source node ID.
            NodeResourceLimitExceededError: If any resource limit is exceeded:
                - Node size > config.max_node_size
                - Network size > config.max_network_size
            FileNotFoundError: If root file does not exist
            FormatDetectionError: If format cannot be detected for any node
            FormatParseError: If parsing fails for any node

        Example:
            >>> builder = NodeNetworkBuilder()
            >>> config = NetworkConfig(max_depth=5)
            >>> network = builder.build_network(Path("prompts/research.yaml"), config)
            >>> print(f"Network has {len(network.nodes)} nodes")
            Network has 5 nodes
        """
        if config is None:
            config = NetworkConfig()

        # Resolve root path with version if provided
        root_node_path = root_path
        if version is not None:
            # If root_path is a directory, use version scanner to resolve versioned file
            if root_path.is_dir():
                from promptic.versioning import VersionedFileScanner

                scanner = VersionedFileScanner()
                try:
                    resolved_file = scanner.resolve_version(str(root_path), version)
                    root_node_path = Path(resolved_file)
                except Exception:
                    # If version resolution fails, fall back to original path
                    pass

        # Load root node using format parser registry
        from promptic.sdk.nodes import load_node

        root_node = load_node(root_node_path)

        # Build network starting from root
        nodes: dict[str, ContextNode] = {}
        visited: set[str] = set()
        recursion_stack: set[str] = set()

        # Determine network root for relative path resolution
        network_root = root_path.parent if root_path.is_file() else root_path

        # Traverse network and build node dictionary
        self._build_network_recursive(
            root_node,
            network_root,  # Use network root for all relative path resolution
            network_root,  # Pass network root separately to maintain it through recursion
            nodes,
            visited,
            recursion_stack,
            config,
            version,  # Pass version for version-aware reference resolution
            depth=0,
        )

        # Calculate network metrics
        total_size = sum(len(str(node.content).encode("utf-8")) for node in nodes.values())

        # Check per-node size limits
        for node in nodes.values():
            node_size = len(str(node.content).encode("utf-8"))
            if node_size > config.max_node_size:
                raise NodeResourceLimitExceededError(
                    f"Node {node.id} exceeds size limit: {node_size} > {config.max_node_size}",
                    limit_type="node_size",
                    current_value=node_size,
                    max_value=config.max_node_size,
                )

        # Check network size limit
        if len(nodes) > config.max_network_size:
            raise NodeResourceLimitExceededError(
                f"Network size exceeds limit: {len(nodes)} > {config.max_network_size}",
                limit_type="network_size",
                current_value=len(nodes),
                max_value=config.max_network_size,
            )

        # Calculate depth
        network_depth = self._calculate_depth(root_node, nodes)

        # Create network
        network = NodeNetwork(
            root=root_node,
            nodes=nodes,
            total_size=total_size,
            depth=network_depth,
        )

        return network

    def _build_network_recursive(
        self,
        node: ContextNode,
        base_path: Path,
        network_root: Path,
        nodes: dict[str, ContextNode],
        visited: set[str],
        recursion_stack: set[str],
        config: NetworkConfig,
        version: Optional[VersionSpec],
        depth: int,
    ) -> None:
        """Recursively build network by loading referenced nodes.

        # AICODE-NOTE: Network traversal and cycle detection algorithm:
        - Uses DFS (depth-first search) with visited set and recursion stack
        - Visited set tracks all nodes seen during traversal
        - Recursion stack tracks nodes in current path (for cycle detection)
        - If a node is in recursion stack, we've found a cycle
        - Depth limit is enforced to prevent stack overflow
        - Relative paths are resolved relative to network_root, not base_path

        Args:
            node: Current node being processed
            base_path: Base path for resolving relative references (deprecated, use network_root)
            network_root: Root directory of the network for resolving relative references
            nodes: Dictionary of all nodes in network (by ID)
            visited: Set of visited node IDs
            recursion_stack: Set of node IDs in current recursion path
            config: Network configuration
            depth: Current depth in network

        Raises:
            NodeNetworkDepthExceededError: If depth limit exceeded
            NodeNetworkValidationError: If cycle detected
            NodeReferenceNotFoundError: If reference cannot be resolved
        """
        node_id = str(node.id)

        # Check depth limit
        if depth > config.max_depth:
            raise NodeNetworkDepthExceededError(
                f"Network depth {depth} exceeds maximum depth {config.max_depth}"
            )

        # Check for cycles (node in recursion stack)
        if node_id in recursion_stack:
            # Build cycle path for error message
            cycle_path = list(recursion_stack) + [node_id]
            cycle_str = " → ".join(cycle_path)
            error = NodeNetworkValidationError(
                f"Circular reference detected: {cycle_str}",
                details={"cycle_path": cycle_path},
            )
            raise error

        # If already visited, skip (but don't add to recursion stack)
        if node_id in visited:
            return

        # Add to visited and recursion stack
        visited.add(node_id)
        recursion_stack.add(node_id)

        # Add node to network
        nodes[node_id] = node

        # Resolve and load referenced nodes
        for ref in node.references:
            try:
                # Validate reference exists (use network_root for relative paths, with version if provided)
                if isinstance(self.resolver, FilesystemReferenceResolver):
                    if not self.resolver.validate(ref.path, network_root, version):
                        raise NodeReferenceNotFoundError(
                            f"Reference not found: {ref.path} (from {node_id})",
                            reference_path=ref.path,
                        )
                else:
                    if not self.resolver.validate(ref.path, network_root):
                        raise NodeReferenceNotFoundError(
                            f"Reference not found: {ref.path} (from {node_id})",
                            reference_path=ref.path,
                        )

                # Resolve reference (use network_root for relative paths, with version if provided)
                if isinstance(self.resolver, FilesystemReferenceResolver):
                    referenced_node = self.resolver.resolve(ref.path, network_root, version)
                else:
                    referenced_node = self.resolver.resolve(ref.path, network_root)

                # Recursively build network for referenced node
                # Always use network_root for relative path resolution
                self._build_network_recursive(
                    referenced_node,
                    base_path,  # Keep for compatibility, but not used for resolution
                    network_root,  # Use network root for all relative path resolution
                    nodes,
                    visited,
                    recursion_stack,
                    config,
                    version,  # Pass version through recursion
                    depth + 1,
                )

                # Add referenced node as child
                if referenced_node.id not in [child.id for child in node.children]:
                    node.children.append(referenced_node)

            except (NodeReferenceNotFoundError, PathResolutionError):
                raise
            except Exception as e:
                raise NodeReferenceNotFoundError(
                    f"Failed to resolve reference {ref.path} from {node_id}: {e}",
                    reference_path=ref.path,
                ) from e

        # Remove from recursion stack (backtrack)
        recursion_stack.remove(node_id)

    def _calculate_depth(self, root: ContextNode, nodes: dict[str, ContextNode]) -> int:
        """Calculate maximum depth of network.

        Args:
            root: Root node
            nodes: All nodes in network

        Returns:
            Maximum depth of network
        """
        visited: set[str] = set()

        def dfs(node: ContextNode, current_depth: int) -> int:
            node_id = str(node.id)
            if node_id in visited:
                return current_depth - 1
            visited.add(node_id)

            max_depth = current_depth
            for child in node.children:
                child_depth = dfs(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)

            return max_depth

        return dfs(root, 1)

    def collect_referenced_files(
        self,
        root_path: Path,
        version: Optional[VersionSpec] = None,
    ) -> set[str]:
        """Collect all files referenced by the network rooted at root_path.

        This method builds the network to resolve all references and versions,
        then returns the set of all file paths involved.

        Args:
            root_path: Path to root node file
            version: Optional version specification

        Returns:
            Set of absolute file paths referenced in the network
        """
        network = self.build_network(root_path, version=version)
        return {str(Path(node_id).resolve()) for node_id in network.nodes}
