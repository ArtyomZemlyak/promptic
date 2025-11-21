# Feature Specification: Unified Context Node Architecture

**Feature Branch**: `004-unified-context-node`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "нужны разные форматы для blueprint и уходим от разделения на инструкции и blueprint"
> This specification MUST satisfy the `promptic Constitution`: clean architecture layering, SOLID responsibilities, mandatory tests, documentation updates, and readability.

**Scope Clarification**: This feature introduces a unified `ContextNode` architecture that abstracts away the distinction between blueprints, instructions, data, and memory. All context elements become recursive `ContextNode` structures that can contain content in multiple formats (YAML, Jinja2, Markdown, JSON) and reference other nodes, forming a network. All formats parse to JSON as the canonical internal representation. This enables flexible composition where any node can reference any other node regardless of its semantic role (instruction, data, memory, blueprint).

**Value Proposition**: The library is useful for complex scenarios (multi-format parsing, cycle detection, programmatic manipulation, extensibility) but the file-first approach can be used without it for simple cases. Simple use cases may only need file structure and reference conventions. The library becomes valuable when: (1) multiple formats need unified parsing and validation, (2) complex networks require cycle detection and depth limiting, (3) programmatic node manipulation is needed, (4) custom parsers or resolvers are required. For simple file-first hierarchies (flat or 2-level structures), basic file references may be sufficient without full library implementation.

**Problems Solved**: Unified architecture provides (1) technical unification (single parser for all formats), (2) flexible composition without rigid categories, (3) easier migration between formats/structures, (4) dynamic semantic changes—nodes can change semantic role (instruction → data, blueprint → memory) without structural changes, enabling runtime flexibility and experimentation.

**Real-World Use Cases**: This architecture addresses practical problems encountered in production systems like tg-note, where prompt management becomes complex without proper structure and composition. Common issues include: (1) monolithic prompt files that are hard to maintain and test, (2) lack of hierarchical organization leading to ad-hoc solutions for connecting prompts, (3) difficulty managing prompt structure and composition programmatically, (4) need for flexible format support (YAML for structure, Markdown for instructions, Jinja2 for templating). The unified ContextNode architecture provides a foundation for solving these problems while maintaining backward compatibility with existing prompt structures.

## Clarifications

### Session 2025-01-27

- Q: How should nodes be uniquely identified and referenced in the network? → A: File path as primary identifier with optional generated IDs for in-memory nodes. Filesystem nodes use paths (e.g., `instructions/think.md`); in-memory/programmatic nodes get generated UUIDs.
- Q: How should node references be expressed in the content of a node file? → A: Format-specific reference syntax. YAML uses `$ref:` syntax, Markdown uses link syntax `[label](path)`, JSON uses structured objects, Jinja2 uses template variables or comments. Each format parser recognizes its native reference syntax and converts to canonical structured format during JSON conversion.
- Q: How should reference paths be resolved—relative to the referencing node or absolute from a root? → A: Relative paths default, absolute paths supported. References are resolved relative to the referencing node's directory by default (e.g., `../sibling.md` or `child/node.md`); absolute paths from a configured root directory are also supported for explicit control.
- Q: Should ContextNode JSON content have a required schema, or is it free-form JSON? → A: Schema-first with free-form fallback. The system attempts to apply schema validation where applicable (based on format, semantic_type, or explicit schema declaration), but if no schema applies or validation fails, content is stored as free-form JSON without structural constraints.
- Q: How should node versioning and updates be handled when source files change? → A: Versioning deferred to future implementation. The `version` field in ContextNode metadata is optional and reserved for future use. Current implementation does not require or enforce versioning. Node updates and version-based caching will be addressed in a later feature.
- Q: Is the library mandatory for the file-first approach, or can the approach be used without it? → A: Library is useful for complex scenarios but approach can be used without it. The file-first approach (hierarchical prompts via file references) can work with simple file structures and manual reference management. The library becomes valuable for: multi-format parsing/validation, cycle detection in complex networks, programmatic node manipulation, versioning, and extensibility (custom parsers, resolvers). Simple use cases may only need the file structure and reference conventions without the full library implementation.
- Q: In which specific scenarios does the library become necessary? → A: Likely combination of validation/parsing + cycle detection (Option C, versioning deferred to future feature), but specific use cases require further research. The boundary between "simple approach" and "library needed" is not yet clearly defined. Practical scenarios where library adds value need to be identified through experimentation and real-world usage patterns. Real-world examples (like tg-note) show that library becomes valuable when: managing complex prompt hierarchies, needing programmatic composition, requiring format validation, or building extensible prompt systems.
- Q: What specific problems does unified ContextNode architecture solve compared to current separation of blueprint/instructions/data/memory? → A: All of the above plus ability to dynamically change node semantics (Option D). Unified architecture provides: (1) Technical unification (single parser for all formats), (2) Flexible composition where any node can reference any other without rigid categories, (3) Easier migration between formats and structures, (4) Dynamic semantic changes—nodes can change their semantic role (instruction → data, blueprint → memory) without structural changes, enabling runtime flexibility and experimentation.
- Q: When are recursive node networks (node → node → node) actually necessary vs. "nice to have"? → A: Only for complex scenarios with deep nesting (3+ levels, Option B). Simple file-first hierarchies (flat or 2-level structures like root → instructions) may not require full recursive network support. Recursive networks become necessary when there's multi-level cross-referencing (instruction → data → memory → another instruction). For simple cases, basic file references may be sufficient without full network traversal and cycle detection.
- Q: Should unified ContextNode architecture be implemented now or start simple and extend later? → A: Implement unified architecture now—it is fundamental (Option A). Despite uncertainty about specific use cases, the unified architecture is considered foundational infrastructure that enables future flexibility. Building it now provides the structural foundation even if some features (like deep recursion) are only used in complex scenarios later. The architecture should be designed to support both simple and complex use cases from the start.
- Q: What memory and resource constraints should be enforced for nodes and networks? → A: Explicit limits with configurable overrides (Option A) plus token-based limits. Default max node size (e.g., 10MB per node), max network size (e.g., 1000 nodes), max tokens per node, and max tokens per network, all configurable per network load operation. Token limits are critical for LLM context management and prevent context overflow issues.
- Q: How should tokens be counted for node and network token limits? → A: Use precise tokenizer (tiktoken) with default model specification (Option A). Token counting uses tiktoken for a specific model (e.g., GPT-4), with configurable model at network level. Counting is performed on final rendered content (after all format conversions) to accurately reflect LLM context usage. The system provides a `TokenCounter` interface with tiktoken-based implementation, allowing model-specific token counting.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-format Context Node Support (Priority: P1)

Context designers can define context nodes in multiple formats (YAML, Jinja2, Markdown, JSON) without being restricted to a single format per node type. All formats are automatically detected and converted to JSON internally for processing.

**Why this priority**: This unlocks the core value proposition—flexibility in authoring context elements without format constraints. Designers can choose the most appropriate format for each node based on content type and authoring preferences. Real-world use cases (like tg-note) show that different parts of a prompt system benefit from different formats: YAML for structured blueprints, Markdown for readable instructions, Jinja2 for templated data, JSON for structured memory. Without multi-format support, designers are forced into monolithic files or ad-hoc format mixing.

**Independent Test**: Starting from an empty workspace, a designer can create four context nodes: one in YAML (blueprint structure), one in Markdown (instruction content), one in Jinja2 (templated data), and one in JSON (structured memory). All nodes load successfully and can be referenced from each other, proving format-agnostic composition.

**Architecture Impact**: Introduces `ContextNode` entity (domain) with format detection and parsing services. Creates format parser registry (`FormatParserRegistry`) with pluggable parsers for each format. All parsers convert their format to JSON as canonical representation. Enforces SRP by separating format detection, parsing, and node composition. Dependency inversion ensures format parsers are pluggable interfaces.

**Quality Signals**: Unit tests for each format parser (YAML, Jinja2, Markdown, JSON), integration test that loads nodes in all formats and verifies JSON conversion, contract tests for format parser interface, docs_site guide "Multi-format context nodes", `# AICODE-NOTE` capturing format detection and parsing rationale.

**Acceptance Scenarios**:

1. **Given** a context node file with `.yaml` extension, **When** it is loaded, **Then** the system detects YAML format, parses it, converts to JSON internally, and creates a `ContextNode` with the parsed content.
2. **Given** a context node file with `.md` extension, **When** it is loaded, **Then** the system detects Markdown format, parses it, converts to JSON internally, and creates a `ContextNode` with the parsed content.
3. **Given** a context node file with `.jinja` or `.jinja2` extension, **When** it is loaded, **Then** the system detects Jinja2 format, parses it (preserving template syntax), converts to JSON internally, and creates a `ContextNode` with the parsed content.
4. **Given** a context node file with `.json` extension, **When** it is loaded, **Then** the system detects JSON format, validates it, and creates a `ContextNode` with the parsed content.

---

### User Story 2 - Recursive Context Node Network (Priority: P2)

Context designers can create recursive node structures where any `ContextNode` can reference and contain other `ContextNode` instances, forming a network. This eliminates the artificial separation between blueprints, instructions, data, and memory—all become nodes in a unified graph.

**Why this priority**: This is the architectural foundation that enables true abstraction from semantic roles. Without recursive composition, nodes remain isolated and the distinction between blueprint/instruction/data/memory persists. However, recursive networks are necessary only for complex scenarios with deep nesting (3+ levels). Simple file-first hierarchies (flat or 2-level structures like root → instructions) may not require full recursive network support. Recursive networks become valuable when there's multi-level cross-referencing (e.g., instruction → data → memory → another instruction), which is common in production systems managing complex prompt structures.

**Independent Test**: A designer creates a root node (YAML blueprint) that references three child nodes: an instruction node (Markdown), a data node (JSON), and a memory node (YAML). One of the child nodes (instruction) itself references another node (nested instruction in Jinja2). The system successfully loads the entire network, validates references, and can render the complete structure, proving recursive composition works across formats.

**Architecture Impact**: Extends `ContextNode` entity to support `children` and `references` fields. Introduces `NodeNetworkBuilder` use case that resolves references and builds the network graph. Adds `NodeReferenceResolver` interface for pluggable reference resolution strategies. Enforces cycle detection to prevent infinite recursion. Uses DIP so network building depends on resolver interfaces rather than concrete implementations.

**Quality Signals**: Unit tests for recursive node loading and reference resolution, integration test building a 3-level deep node network with mixed formats, contract tests for reference resolver interface, validation tests detecting circular references, docs_site guide "Recursive context networks", `# AICODE-NOTE` explaining network traversal and cycle detection.

**Acceptance Scenarios**:

1. **Given** a root node that references three child nodes by path, **When** the network is loaded, **Then** all referenced nodes are loaded, parsed, and linked to the root node, forming a complete network.
2. **Given** a node network with a circular reference (A → B → C → A), **When** the network is loaded, **Then** the system detects the cycle and raises a `NodeNetworkValidationError` with details about the cycle path.
3. **Given** a node that references a non-existent node, **When** the network is loaded, **Then** the system raises a `NodeReferenceNotFoundError` indicating which reference is missing.
4. **Given** a node network with nodes in different formats, **When** the network is rendered, **Then** all nodes are converted to their target format (e.g., all to JSON for internal processing, or to their native format for output) maintaining the network structure.

---

### User Story 3 - Unified Node Abstraction (Priority: P3)

The system abstracts away semantic distinctions between blueprints, instructions, data, and memory. All become `ContextNode` instances that can be composed and referenced uniformly. Existing blueprint/instruction/data/memory concepts are preserved as optional metadata or conventions, not structural requirements.

**Why this priority**: This completes the architectural vision—designers can think in terms of nodes and networks rather than being constrained by rigid categories. However, this can be built incrementally after format support and recursion are working. This abstraction solves real-world problems where prompt systems (like tg-note) struggle with rigid separation between prompt types, leading to ad-hoc solutions for connecting prompts together. Unified abstraction enables flexible composition where any node can reference any other node, solving the "joining prompts together" problem that currently requires custom solutions.

**Independent Test**: A designer creates a workflow where a "blueprint" node (YAML) references an "instruction" node (Markdown) which references a "data" node (JSON) which references a "memory" node (YAML). The system treats all as `ContextNode` instances with no special handling based on semantic role. The network renders successfully, proving the abstraction works. Existing code that expects `ContextBlueprint` and `InstructionNode` continues to work through adapter layers that map old concepts to new nodes.

**Architecture Impact**: Introduces adapter layer (`LegacyBlueprintAdapter`, `LegacyInstructionAdapter`) that maps existing `ContextBlueprint`/`InstructionNode` models to `ContextNode` for backward compatibility. Creates `NodeSemanticTagger` interface for optional semantic labeling (blueprint, instruction, data, memory) without enforcing structural differences. Uses adapter pattern to maintain backward compatibility while enabling new unified architecture. Documents migration path from old to new architecture.

**Quality Signals**: Unit tests for legacy adapters mapping old models to nodes, integration test using existing blueprint YAML files with new node system, backward compatibility tests ensuring existing APIs still work, migration guide in docs_site, `# AICODE-NOTE` explaining adapter strategy and deprecation timeline.

**Acceptance Scenarios**:

1. **Given** an existing blueprint YAML file using the old `ContextBlueprint` schema, **When** it is loaded, **Then** the system uses `LegacyBlueprintAdapter` to convert it to a `ContextNode` network, maintaining full functionality.
2. **Given** a new node network created with the unified architecture, **When** it is accessed via legacy APIs expecting `ContextBlueprint`, **Then** the system uses `LegacyBlueprintAdapter` to present the network as a blueprint, ensuring backward compatibility.
3. **Given** a node network where nodes have no semantic labels, **When** the network is rendered, **Then** the system processes all nodes uniformly without requiring blueprint/instruction/data/memory distinctions.
4. **Given** a node network where nodes have optional semantic metadata (e.g., `semantic_type: "instruction"`), **When** the network is rendered, **Then** the system can use this metadata for specialized rendering or validation, but does not require it for basic functionality.

---

### Edge Cases

- **Format detection ambiguity**: When a file extension matches multiple formats (e.g., `.md` could be Markdown or a custom format), the system uses content-based detection (magic bytes, structure analysis) and falls back to explicit format declaration in metadata. If detection fails, raises `FormatDetectionError` with suggested format hints.
- **Reference syntax parsing errors**: When a format parser encounters malformed reference syntax (e.g., invalid `$ref:` in YAML, broken link in Markdown), it raises `ReferenceSyntaxError` with format-specific guidance. Parsers should be lenient where possible (e.g., treat plain text paths as potential references) but validate structure during JSON conversion.
- **Circular references in node network**: Network builder detects cycles using depth-first search with visited set, raises `NodeNetworkValidationError` with full cycle path (e.g., "A → B → C → A") for debugging. Configurable max depth limit (default 10 levels) prevents stack overflow from extremely deep but valid trees.
- **Missing referenced nodes**: When a node references another node by path/ID and the target doesn't exist, raises `NodeReferenceNotFoundError` with the missing reference path and suggestions for similar existing nodes. Optional fallback policy (similar to instruction fallback) can inject placeholder nodes.
- **Path resolution failures**: When a relative path cannot be resolved (e.g., `../nonexistent.md` from root node, or path escapes root directory), raises `PathResolutionError` with the attempted path and base directory context. Absolute paths that fall outside configured root also raise `PathResolutionError`.
- **Format parsing errors**: When a file claims to be a format (by extension or metadata) but parsing fails, raises `FormatParseError` with line numbers and specific syntax issues. Provides helpful error messages suggesting common fixes (e.g., "YAML syntax error: unexpected indentation at line 5").
- **JSON conversion failures**: When a format cannot be converted to JSON (e.g., binary content, invalid structure), raises `JSONConversionError` with details about what prevented conversion. Some formats (e.g., raw text) may convert to JSON string values rather than structured objects.
- **Recursive depth limits**: When a node network exceeds configured max depth (default 10), network builder stops traversal and raises `NodeNetworkDepthExceededError`. This prevents infinite recursion from bugs while allowing legitimate deep hierarchies. Depth limit is configurable per network load operation.
- **Resource limit violations**: When a node exceeds max size (default 10MB) or max tokens per node, or when a network exceeds max network size (default 1000 nodes) or max tokens per network, the system raises `NodeResourceLimitExceededError` with details about which limit was violated, current value, and maximum allowed value. Token counting uses tiktoken with configurable model specification and is performed on final rendered content (after all format conversions) to accurately reflect LLM context usage. All limits are configurable per network load operation, allowing different limits for different use cases. If tiktoken fails to count tokens (e.g., unsupported model), the system raises `TokenCountingError` with model information.
- **Backward compatibility breaks**: When existing code expects `ContextBlueprint` but receives `ContextNode`, adapter layer provides transparent conversion. If conversion is impossible (e.g., node structure doesn't match blueprint schema), raises `LegacyAdapterError` with migration guidance. All existing tests must pass with adapter layer enabled.
- **Format parser registration conflicts**: When multiple parsers claim to handle the same format/extension, registry uses explicit priority or first-registered-wins strategy. Raises warning during registration, allows override via explicit parser selection in node metadata.
- **Schema validation failures**: When schema validation is attempted but fails (content doesn't match schema), the system stores content as free-form JSON and continues processing. Schema validation errors are logged as warnings but do not block node loading or network construction. Nodes with schema validation failures remain fully functional.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support loading context nodes from files in multiple formats: YAML (`.yaml`, `.yml`), Jinja2 (`.jinja`, `.jinja2`), Markdown (`.md`, `.markdown`), and JSON (`.json`). Format detection MUST work via file extension and content analysis.
- **FR-002**: The system MUST convert all format inputs to JSON as the canonical internal representation. Parsed content MUST be stored as JSON within `ContextNode` entities, regardless of source format.
- **FR-003**: The system MUST support recursive node structures where any `ContextNode` can contain or reference other `ContextNode` instances, forming a network graph. References MUST be resolved during network loading.
- **FR-004**: The system MUST abstract away semantic distinctions between blueprints, instructions, data, and memory. All MUST be represented as `ContextNode` instances with optional semantic metadata, not structural requirements.
- **FR-005**: The system MUST provide format parser registry (`FormatParserRegistry`) with pluggable parser interfaces. Each format MUST have a dedicated parser implementing `FormatParser` interface that handles detection, parsing, and JSON conversion.
- **FR-006**: The system MUST detect and prevent circular references in node networks. Cycle detection MUST use graph traversal algorithms and raise `NodeNetworkValidationError` with cycle path details when cycles are found.
- **FR-007**: The system MUST enforce configurable depth limits for recursive node networks (default 10 levels) to prevent stack overflow and infinite recursion bugs. Depth limit MUST be configurable per network load operation.
- **FR-007a**: The system MUST enforce configurable resource limits: max node size (default 10MB per node), max network size (default 1000 nodes), max tokens per node, and max tokens per network. All limits MUST be configurable per network load operation. Token limits are critical for LLM context management and prevent context overflow. When limits are exceeded, the system MUST raise `NodeResourceLimitExceededError` with details about which limit was violated and the current vs. maximum values.
- **FR-007b**: The system MUST count tokens using tiktoken with a configurable model specification (default model, e.g., GPT-4). Token counting MUST be performed on final rendered content (after all format conversions) to accurately reflect LLM context usage. The system MUST provide a `TokenCounter` interface with tiktoken-based implementation, allowing model-specific token counting. The model for token counting MUST be configurable at network load operation level, enabling different models for different use cases.
- **FR-008**: The system MUST provide backward compatibility adapters (`LegacyBlueprintAdapter`, `LegacyInstructionAdapter`) that map existing `ContextBlueprint`/`InstructionNode` models to `ContextNode` networks, ensuring existing code and APIs continue to work.
- **FR-009**: The system MUST support optional semantic labeling of nodes (e.g., `semantic_type: "instruction"`) without requiring it for basic functionality. Semantic labels MUST be metadata only and not affect node structure or network composition.
- **FR-010**: The system MUST validate node references during network loading. Missing references MUST raise `NodeReferenceNotFoundError` with the missing path and suggestions. Reference resolution MUST support both file paths (primary for filesystem nodes) and generated IDs (for in-memory/programmatic nodes). Filesystem nodes are identified by their file path; in-memory nodes use generated UUIDs.
- **FR-011**: The system MUST provide `NodeNetworkBuilder` use case that orchestrates node loading, reference resolution, and network graph construction. Builder MUST depend on `NodeReferenceResolver` interface for pluggable resolution strategies.
- **FR-012**: The system MUST preserve format-specific features during parsing and conversion. Jinja2 templates MUST preserve template syntax in JSON (e.g., as string values with `{{ }}` markers), Markdown MUST preserve structure (headings, lists) in JSON representation, YAML MUST preserve hierarchy in JSON objects/arrays.
- **FR-015**: The system MUST support format-specific reference syntax. YAML nodes use `$ref:` syntax (e.g., `$ref: instructions/think.md`), Markdown nodes use link syntax `[label](path)` (e.g., `[See instructions](instructions/think.md)`), JSON nodes use structured reference objects (e.g., `{"type": "reference", "path": "instructions/think.md"}`), Jinja2 nodes use template variables or comments. Each format parser MUST recognize its native reference syntax and convert references to canonical structured format during JSON conversion.
- **FR-016**: The system MUST resolve reference paths relative to the referencing node's directory by default (e.g., `../sibling.md` resolves relative to the node's parent directory). The system MUST also support absolute paths from a configured root directory when explicitly specified. Path resolution MUST handle both relative and absolute references correctly during network building.
- **FR-017**: The system MUST attempt to apply schema validation to ContextNode JSON content where applicable (based on format, semantic_type metadata, or explicit schema declaration). If no schema applies or validation fails, content MUST be stored as free-form JSON without structural constraints. Schema validation is optional and non-blocking—nodes with unvalidated or free-form content remain fully functional.
- **FR-013**: The system MUST support format-specific rendering where nodes can be output in their native format (YAML, Markdown, etc.) or converted to a target format, maintaining network structure and references.
- **FR-014**: The system MUST provide migration path documentation and tooling for converting existing blueprints/instructions to unified node format, with validation to ensure no information loss during conversion.

### Key Entities *(include if feature involves data)*

- **ContextNode**: Unified domain entity representing any context element (blueprint, instruction, data, memory). Contains format-agnostic content (stored as JSON), metadata (format, semantic_type, optional version field reserved for future use), and references to other nodes. Supports recursive composition where nodes can contain or reference other nodes. Identity: filesystem nodes are identified by file path (e.g., `instructions/think.md`); in-memory/programmatic nodes use generated UUIDs. References can use either path or ID depending on node source. Content structure: system attempts schema validation where applicable, but falls back to free-form JSON if no schema applies or validation fails. Resource limits: nodes are subject to size limits (default 10MB) and token limits (configurable per node) to prevent context overflow. Token counting is performed on final rendered content (after all format conversions) using tiktoken with configurable model specification to accurately reflect LLM context usage. Versioning: version field exists in metadata but is not enforced or used in current implementation; versioning will be addressed in a future feature.
- **FormatParser**: Interface for format-specific parsing. Each parser implements detection (identifies format from file/content), parsing (extracts structured content), and JSON conversion (transforms to canonical JSON representation). Parsers must recognize format-specific reference syntax (YAML `$ref:`, Markdown links, JSON objects, Jinja2 variables) and convert to canonical structured format. Parsers are pluggable and registered in `FormatParserRegistry`.
- **FormatParserRegistry**: Service that manages format parser registration and selection. Maps file extensions and format names to parser implementations. Provides format detection by trying registered parsers in priority order.
- **NodeNetworkBuilder**: Use case that orchestrates loading multiple nodes, resolving references, and constructing the network graph. Depends on `NodeReferenceResolver` interface for reference resolution strategies and `TokenCounter` interface for token counting. Validates network structure (cycles, depth limits, missing references) and enforces resource limits (node size, network size, token limits per node and per network). Token counting uses `TokenCounter` with configurable model specification. Raises `NodeResourceLimitExceededError` when any limit is exceeded during network construction.
- **NodeReferenceResolver**: Interface for pluggable reference resolution strategies. Implementations handle different reference types (file paths, node IDs, URIs) and resolve them to actual `ContextNode` instances. Must support relative path resolution (from referencing node's directory) and absolute path resolution (from configured root). Enables flexible reference schemes without hardcoding filesystem assumptions.
- **TokenCounter**: Interface for token counting with tiktoken-based implementation. Provides model-specific token counting using tiktoken library, with configurable model specification (default model, e.g., GPT-4). Token counting is performed on final rendered content (after all format conversions) to accurately reflect LLM context usage. Model for token counting is configurable at network load operation level, enabling different models for different use cases.
- **LegacyBlueprintAdapter**: Adapter that converts existing `ContextBlueprint` models to `ContextNode` networks for backward compatibility. Maps blueprint structure (steps, instructions, data slots) to node network with appropriate references and metadata.
- **LegacyInstructionAdapter**: Adapter that converts existing `InstructionNode` models to `ContextNode` instances for backward compatibility. Preserves instruction metadata and content while using unified node structure.

### Architecture & Quality Constraints *(from Constitution)*

- **AQ-001**: Keep `ContextNode`, `FormatParser` interface, and `NodeNetworkBuilder` in domain/use-case layers; format parser implementations and filesystem reference resolvers in adapter layer. Use dependency inversion so network building depends on `NodeReferenceResolver` interface, not concrete filesystem implementations.
- **AQ-002**: Apply SRP by separating format detection, parsing, JSON conversion, reference resolution, and network building into distinct classes. Document intentional coupling (e.g., parser registry knowing about all parsers) via `# AICODE-NOTE`. Use adapter pattern for backward compatibility to avoid mixing old and new architectures in same modules.
- **AQ-003**: Provide unit tests for each format parser (YAML, Jinja2, Markdown, JSON), `NodeNetworkBuilder` with mocked resolvers, cycle detection, depth limit enforcement, and legacy adapters. Integration tests loading multi-format node networks, recursive structures, and backward compatibility scenarios. Contract tests for `FormatParser` and `NodeReferenceResolver` interfaces. All run via `pytest` in CI.
- **AQ-004**: Update docs_site with "Multi-format context nodes" guide, "Recursive node networks" guide, "Unified node architecture" overview, migration guide from old to new architecture, and format parser extension guide. Update inline docstrings for all new entities and use cases. Add `# AICODE-NOTE` comments explaining format detection strategy, JSON conversion rationale, and backward compatibility approach. Resolve any `# AICODE-ASK` prompts before merge.
- **AQ-005**: Enforce readability by limiting public functions to <100 logical lines, using descriptive names (e.g., `detect_format_from_content`, `build_node_network_from_references`), and deleting experimental code after each milestone. Format parser implementations should be focused and testable in isolation.

### Assumptions

- JSON is the canonical internal format because it's universal, supports nested structures, and integrates well with existing Pydantic models. All format parsers convert their format to JSON, enabling uniform processing regardless of source format.
- Recursive node networks are the primary composition mechanism. While this enables powerful flexibility, it also requires careful cycle detection and depth limiting to prevent bugs and performance issues.
- Resource limits (node size, network size, token limits) are enforced to prevent context overflow and memory issues. Default limits (10MB per node, 1000 nodes per network, plus token limits) are conservative and can be overridden per network load operation. Token counting uses tiktoken library with configurable model specification (default model, e.g., GPT-4) and is performed on final rendered content (after all format conversions) to accurately reflect LLM context usage, as this is the critical constraint for LLM integration. The model for token counting is configurable at network load operation level, enabling different models for different use cases.
- Backward compatibility is maintained through adapter layers rather than modifying existing `ContextBlueprint`/`InstructionNode` models. This allows incremental migration and reduces risk of breaking existing code.
- Format-specific features (e.g., Jinja2 template syntax) are preserved in JSON representation as structured data (e.g., template strings with markers) rather than being lost during conversion. This enables round-trip conversion and format-specific rendering.
- Semantic labeling (blueprint, instruction, data, memory) is optional metadata, not a structural requirement. This allows designers to use nodes flexibly while still supporting specialized tooling that understands semantic roles.
- Reference resolution supports file paths as the primary mechanism initially, with extensibility for node IDs, URIs, and other schemes via pluggable resolvers. This balances simplicity with future flexibility.
- **Library value proposition**: The library is useful for complex scenarios (validation/parsing + cycle detection + programmatic manipulation + extensibility) but specific use cases where it becomes necessary vs. optional are not yet clearly defined. The boundary between "simple file-first approach" and "library needed" requires further research through practical experimentation and real-world usage patterns. Real-world examples (like tg-note integration) demonstrate that library becomes valuable when managing complex prompt hierarchies, needing programmatic composition, requiring format validation, or building extensible systems. Versioning is explicitly deferred to a future feature and not part of this implementation.
- **Recursive networks scope**: Recursive node networks are necessary only for complex scenarios with deep nesting (3+ levels). Simple file-first hierarchies (flat or 2-level structures) may not require full recursive network support with cycle detection and depth limiting. Recursive networks become valuable when there's multi-level cross-referencing (e.g., instruction → data → memory → another instruction). For simple cases, basic file references may be sufficient without full network traversal infrastructure. Real-world examples show that most production systems start with simple hierarchies and evolve to complex networks as requirements grow, so the architecture must support both from the start.
- **Implementation priority**: Unified ContextNode architecture should be implemented now as fundamental infrastructure (Option A). Despite uncertainty about specific use cases, the unified architecture is foundational and enables future flexibility. Building it now provides structural foundation even if some features (like deep recursion) are primarily used in complex scenarios later. The architecture should support both simple and complex use cases from the start.

## Practical Use Cases & Integration Examples

### Real-World Problem: tg-note Integration

**Problem Statement**: The tg-note project (Telegram bot for GitHub knowledge base) faces challenges with prompt management:
- Monolithic prompt files that are hard to maintain and test
- Lack of hierarchical organization leading to ad-hoc solutions for connecting prompts
- Difficulty managing prompt structure and composition programmatically
- Need for flexible format support (YAML for structure, Markdown for instructions, Jinja2 for templating)

**How Unified ContextNode Architecture Solves This**:

1. **Multi-format Support**: Different parts of the prompt system can use appropriate formats:
   - YAML for structured blueprints (`note_creation.yaml`)
   - Markdown for readable instructions (`instructions/analyze.md`)
   - Jinja2 for templated data (`templates/data.jinja2`)
   - JSON for structured memory (`memory/format.json`)

2. **Hierarchical Composition**: Prompts can be organized in a clear hierarchy:
   ```
   config/prompts/
   ├── note_creation.yaml          # Root blueprint
   ├── instructions/
   │   ├── analyze.md              # Referenced instruction
   │   ├── create_note.md          # Referenced instruction
   │   └── media.md                # Referenced instruction (may reference OCR files)
   └── memory/
       └── format.md               # Memory format specification
   ```

3. **Flexible References**: Any node can reference any other node, solving the "joining prompts together" problem:
   - Root blueprint references instruction nodes
   - Instruction nodes can reference data nodes
   - Data nodes can reference memory nodes
   - Memory nodes can reference other instructions (for format specifications)

4. **Programmatic Access**: The library provides APIs for loading, composing, and rendering node networks, enabling integration with systems like tg-note that need to programmatically manage prompts.

**Integration Example**:
```python
from promptic import load_blueprint, render_for_llm

# Load unified node network
blueprint = load_blueprint("config/prompts/note_creation.yaml")

# Render compact prompt with file-first approach
compact_prompt = render_for_llm(blueprint, render_mode="file_first")

# Pass to qwen code cli - agent receives compact prompt with references
# Agent decides which instructions to read based on context
response = qwen_code_cli.run(compact_prompt)
```

### When Library Becomes Necessary

**Simple Cases (Library Optional)**:
- Flat file structure with basic references (root → instructions)
- Manual reference management is acceptable
- Single format (e.g., all Markdown)
- No need for programmatic composition

**Complex Cases (Library Recommended)**:
- Multi-format support needed (YAML + Markdown + Jinja2)
- Complex hierarchies with 3+ levels of nesting
- Need for cycle detection and validation
- Programmatic node manipulation required
- Custom parsers or resolvers needed
- Integration with external systems (like tg-note)

**Boundary Example**: A simple 2-level hierarchy (root blueprint → instruction files) can work with basic file references. When the system grows to include data nodes, memory nodes, and cross-references between them, the library's cycle detection, validation, and programmatic APIs become valuable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Designers can create context nodes in all four supported formats (YAML, Jinja2, Markdown, JSON) and load them successfully. Format detection accuracy is >95% for files with standard extensions.
- **SC-002**: All format inputs convert to JSON successfully with no data loss for supported structures. Round-trip conversion (format → JSON → format) preserves content structure for YAML, JSON, and Markdown (Jinja2 templates preserved as template strings).
- **SC-003**: Designers can create recursive node networks with at least 3 levels of nesting, mixing formats at each level. Network loading completes in <2 seconds for networks with <50 nodes.
- **SC-004**: Cycle detection identifies 100% of circular references in test networks and provides actionable error messages with cycle paths. Depth limit enforcement prevents stack overflow for networks exceeding configured limits.
- **SC-004a**: Resource limit validation catches 100% of violations (node size, network size, token limits per node and per network) before network construction completes. Token counting uses tiktoken with configurable model specification and accurately reflects LLM context usage on final rendered content (after all format conversions). All limits are configurable and can be overridden per network load operation. Error messages clearly indicate which limit was exceeded and provide current vs. maximum values. Token counting supports multiple models (e.g., GPT-4, GPT-3.5-turbo) with model selection configurable per network load operation.
- **SC-005**: Backward compatibility adapters successfully convert 100% of existing blueprint/instruction test cases to node networks without functionality loss. All existing integration tests pass with adapters enabled.
- **SC-006**: All related pytest suites (unit, integration, contract) pass locally and in CI with evidence linked in the PR. Test coverage for new node architecture is >80% for core use cases.
- **SC-007**: Relevant docs_site pages are updated with multi-format guide, recursive networks guide, unified architecture overview, and migration guide. All new entities and use cases have comprehensive docstrings.
- **SC-008**: Format parser registry supports adding new format parsers via plugin registration without modifying core code. At least one custom format parser (beyond the four built-in) can be registered and used in integration tests.
- **SC-009**: Node network validation catches >95% of structural issues (missing references, cycles, depth violations) before rendering, providing clear error messages that help designers fix problems quickly.
