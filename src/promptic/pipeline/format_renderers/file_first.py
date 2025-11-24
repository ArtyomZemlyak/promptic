from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from promptic.blueprints.adapters.legacy import node_to_instruction
from promptic.blueprints.models import (
    BlueprintStep,
    ContextBlueprint,
    InstructionNode,
    InstructionNodeRef,
    InstructionReference,
    MemoryChannel,
    PromptHierarchyBlueprint,
    RenderMetrics,
)
from promptic.blueprints.serialization import (
    FileFirstMetadata,
    build_reference_id,
    estimate_token_count,
    get_file_first_metadata,
)
from promptic.context.errors import InstructionNotFoundError, TemplateRenderError
from promptic.context.nodes.models import ContextNode
from promptic.instructions.store import MemoryDescriptorCollector
from promptic.pipeline.context_materializer import ContextMaterializer


@dataclass
class FileFirstRenderResult:
    """Container returned by file-first rendering strategy."""

    markdown: str
    metadata: PromptHierarchyBlueprint
    warnings: list[str] = field(default_factory=list)


@dataclass
class SummaryResult:
    instruction_id: str
    reference_path: str
    summary: str
    token_estimate: int


@dataclass
class ReferenceTreeResult:
    references: list[InstructionReference]
    warnings: list[str] = field(default_factory=list)
    missing_paths: list[str] = field(default_factory=list)


class FileSummaryService:
    """Summarizes file-based instructions before they are referenced."""

    def __init__(
        self,
        *,
        materializer: ContextMaterializer,
        max_tokens: int = 120,
        overrides: Mapping[str, str] | None = None,
    ) -> None:
        self._materializer = materializer
        self._max_tokens = max_tokens
        self._instruction_root = materializer.settings.resolved_instruction_root()
        self._overrides = {self._normalize_key(k): v for k, v in (overrides or {}).items()}
        self._cache: Dict[str, SummaryResult] = {}

    def summarize(self, instruction_id: str, version: Optional[str] = None) -> SummaryResult:
        cache_key = f"{instruction_id}:{version}" if version else instruction_id
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        result = self._materializer.resolve_instruction(instruction_id, version=version)
        if not result.ok:
            raise InstructionNotFoundError(instruction_id)
        node, content = result.unwrap()
        relative_path = self._relative_path(node)
        override = self._lookup_override(instruction_id, relative_path)
        summary = override or self._truncate(content)
        token_estimate = estimate_token_count(content)
        payload = SummaryResult(
            instruction_id=instruction_id,
            reference_path=relative_path,
            summary=summary,
            token_estimate=token_estimate,
        )
        self._cache[cache_key] = payload
        return payload

    def _lookup_override(self, instruction_id: str, relative_path: str) -> str | None:
        candidates = [
            self._normalize_key(instruction_id),
            self._normalize_key(relative_path),
            self._normalize_key(Path(relative_path).with_suffix("").as_posix()),
        ]
        for candidate in candidates:
            override = self._overrides.get(candidate)
            if override:
                return override
        return None

    def _truncate(self, content: str) -> str:
        tokens = content.replace("\n", " ").split()
        if len(tokens) <= self._max_tokens:
            return " ".join(tokens).strip()
        return " ".join(tokens[: self._max_tokens]).strip() + "..."

    def _relative_path(self, node: InstructionNode | ContextNode) -> str:
        # Convert ContextNode to InstructionNode for compatibility during migration
        if isinstance(node, ContextNode):
            node = node_to_instruction(node)

        source = Path(str(node.source_uri)).resolve()
        try:
            relative = source.relative_to(self._instruction_root.resolve())
        except ValueError:
            return source.name
        return relative.as_posix()

    @staticmethod
    def _normalize_key(value: str) -> str:
        return value.strip().lower().replace("\\", "/")


class ReferenceFormatter:
    """Converts instruction metadata into human-readable reference text."""

    def __init__(self, *, base_url: str | None = None) -> None:
        self._base_url = base_url.rstrip("/") if base_url else None

    def format_path(self, relative_path: str) -> str:
        if not self._base_url:
            return relative_path
        return f"{self._base_url}/{relative_path}"

    def detail_hint(self, relative_path: str) -> str:
        target = self.format_path(relative_path)
        return f"See more: {target}"


class ReferenceTreeBuilder:
    """Builds nested InstructionReference trees with cycle/depth checks."""

    def __init__(
        self,
        *,
        blueprint: ContextBlueprint,
        summary_service: FileSummaryService,
        formatter: ReferenceFormatter,
        depth_limit: int = 3,
    ) -> None:
        if depth_limit < 1:
            raise ValueError("depth_limit must be >= 1")
        self._blueprint = blueprint
        self._summary_service = summary_service
        self._formatter = formatter
        self._depth_limit = depth_limit
        self._warnings: list[str] = []
        self._missing_paths: set[str] = set()

    def build(self) -> ReferenceTreeResult:
        references: list[InstructionReference] = []
        for step in self._blueprint.steps:
            references.extend(self._build_step(step, depth=1, lineage=[]))
        return ReferenceTreeResult(
            references=references,
            warnings=list(self._warnings),
            missing_paths=sorted(self._missing_paths),
        )

    def _build_step(
        self,
        step: BlueprintStep,
        *,
        depth: int,
        lineage: list[str],
    ) -> list[InstructionReference]:
        if depth > self._depth_limit:
            self._warnings.append(
                f"Depth limit reached at step '{step.step_id}' (limit {self._depth_limit})."
            )
            return []
        if step.step_id in lineage:
            self._warnings.append(f"Cycle detected at step '{step.step_id}'.")
            return []

        updated_lineage = lineage + [step.step_id]
        references: list[InstructionReference] = []
        if step.instruction_refs:
            primary = self._build_reference(step, step.instruction_refs[0])
            if primary:
                extra_children: list[InstructionReference] = []
                for ref in step.instruction_refs[1:]:
                    child = self._build_reference(step, ref, is_secondary=True)
                    if child:
                        extra_children.append(child)
                child_steps = self._collect_child_references(step.children, depth, updated_lineage)
                primary.children.extend(extra_children + child_steps)
                references.append(primary)
        else:
            references.extend(self._collect_child_references(step.children, depth, updated_lineage))
        return references

    def _collect_child_references(
        self,
        children: Sequence[BlueprintStep],
        depth: int,
        lineage: list[str],
    ) -> list[InstructionReference]:
        aggregated: list[InstructionReference] = []
        for child in children:
            aggregated.extend(self._build_step(child, depth=depth + 1, lineage=lineage))
        return aggregated

    def _build_reference(
        self,
        step: BlueprintStep,
        node_ref: InstructionNodeRef,
        *,
        is_secondary: bool = False,
    ) -> InstructionReference | None:
        try:
            summary = self._summary_service.summarize(
                node_ref.instruction_id, version=node_ref.version
            )
        except InstructionNotFoundError:
            self._missing_paths.add(node_ref.instruction_id)
            return None

        title = step.title if not is_secondary else f"{step.title} ({node_ref.instruction_id})"
        reference_path = summary.reference_path
        detail_hint = self._formatter.detail_hint(reference_path)
        identifier = build_reference_id(reference_path)
        return InstructionReference(
            id=identifier,
            title=title,
            summary=summary.summary,
            reference_path=self._formatter.format_path(reference_path),
            detail_hint=detail_hint,
            token_estimate=summary.token_estimate,
        )


class RenderMetricsBuilder:
    """Tracks token deltas and reference statistics."""

    def build(
        self,
        *,
        markdown: str,
        references: Sequence[InstructionReference],
        missing_paths: Sequence[str],
    ) -> RenderMetrics:
        tokens_before = self._sum_tokens(references)
        tokens_after = estimate_token_count(markdown)
        reference_count = self._count_references(references)
        return RenderMetrics(
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            reference_count=reference_count,
            missing_paths=list(missing_paths),
        )

    def _sum_tokens(self, references: Sequence[InstructionReference]) -> int:
        total = 0
        for ref in references:
            total += max(ref.token_estimate, 0)
            if ref.children:
                total += self._sum_tokens(ref.children)
        return total

    def _count_references(self, references: Sequence[InstructionReference]) -> int:
        count = 0
        for ref in references:
            count += 1
            if ref.children:
                count += self._count_references(ref.children)
        return count


class FileFirstRenderer:
    """
    High-level coordinator for persona/goals markdown and metadata payloads.

    # AICODE-NOTE: This strategy is registered inside TemplateRenderer so callers
    #              can request `render_mode="file_first"` without coupling to the
    #              underlying helper classes.
    """

    def __init__(self, *, max_summary_tokens: int = 120) -> None:
        self._max_summary_tokens = max_summary_tokens
        self._metrics_builder = RenderMetricsBuilder()

    def render(
        self,
        *,
        blueprint: ContextBlueprint,
        materializer: ContextMaterializer,
        base_url: str | None,
        depth_limit: int,
        summary_overrides: Mapping[str, str],
    ) -> FileFirstRenderResult:
        metadata = get_file_first_metadata(blueprint)
        overrides = dict(metadata.summary_overrides)
        overrides.update({k.lower(): v for k, v in summary_overrides.items()})

        summary_service = FileSummaryService(
            materializer=materializer,
            max_tokens=self._max_summary_tokens,
            overrides=overrides,
        )
        formatter = ReferenceFormatter(base_url=base_url)
        tree_builder = ReferenceTreeBuilder(
            blueprint=blueprint,
            summary_service=summary_service,
            formatter=formatter,
            depth_limit=depth_limit,
        )
        tree = tree_builder.build()
        if tree.missing_paths:
            raise TemplateRenderError(
                instruction_id="__file_first__",
                format="file_first",
                error_type="missing_assets",
                message="Referenced instruction files are missing.",
                context={"missing": tree.missing_paths},
            )

        hierarchy = PromptHierarchyBlueprint(
            blueprint_id=str(blueprint.id),
            persona=metadata.persona,
            objectives=metadata.objectives,
            steps=tree.references,
            memory_channels=self._build_memory_channels(blueprint, materializer),
        )
        markdown = self._render_markdown(
            persona=metadata.persona,
            objectives=metadata.objectives,
            references=tree.references,
            memory_channels=hierarchy.memory_channels,
        )
        metrics = self._metrics_builder.build(
            markdown=markdown,
            references=hierarchy.steps,
            missing_paths=tree.missing_paths,
        )
        hierarchy.metrics = metrics
        return FileFirstRenderResult(markdown=markdown, metadata=hierarchy, warnings=tree.warnings)

    def _build_memory_channels(
        self,
        blueprint: ContextBlueprint,
        materializer: ContextMaterializer,
    ) -> list[MemoryChannel]:
        collector = MemoryDescriptorCollector(
            instruction_root=materializer.settings.resolved_instruction_root()
        )
        return collector.collect(blueprint)

    def _render_markdown(
        self,
        *,
        persona: str,
        objectives: Sequence[str],
        references: Sequence[InstructionReference],
        memory_channels: Sequence[MemoryChannel],
    ) -> str:
        lines: list[str] = [
            "## Persona",
            persona.strip(),
            "",
            "### Objectives",
        ]
        for idx, goal in enumerate(objectives, start=1):
            lines.append(f"{idx}. {goal}")
        lines.append("")
        lines.append("### Steps")
        lines.extend(self._render_reference_lines(references, level=0))
        if memory_channels:
            lines.append("")
            lines.append("### Memory & Logging")
            for channel in memory_channels:
                descriptor = (
                    f" (descriptor: {channel.format_descriptor_path})"
                    if channel.format_descriptor_path
                    else ""
                )
                lines.append(f"- {channel.location} — {channel.expected_format}{descriptor}")
        return "\n".join(lines).strip()

    def _render_reference_lines(
        self,
        references: Sequence[InstructionReference],
        *,
        level: int,
    ) -> list[str]:
        lines: list[str] = []
        prefix = "  " * level + "-"
        for ref in references:
            lines.append(f"{prefix} **{ref.title}** — {ref.summary} ({ref.detail_hint})")
            if ref.children:
                lines.extend(self._render_reference_lines(ref.children, level=level + 1))
        return lines


__all__ = [
    "FileFirstRenderResult",
    "FileFirstRenderer",
    "FileSummaryService",
    "ReferenceFormatter",
    "ReferenceTreeBuilder",
    "ReferenceTreeResult",
    "RenderMetricsBuilder",
]
