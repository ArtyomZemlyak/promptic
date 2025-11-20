# Feature Specification: File-First Prompt Hierarchy

**Feature Branch**: `003-file-first-prompts`  
**Created**: 2025-11-20  
**Status**: Draft  
**Input**: User description: "смотри readme для того что нужно уточнить. То есть, вот нужно описанный мной кейс максимально автоматизировать"
> This specification operationalizes the README vision: prompts are stored as files, while the LLM receives only a compact root instruction that lists persona, goals, steps, and pointers toward richer files when deeper context is needed.

## Clarifications

### Session 2025-11-20

- Q: What structure should the emitted metadata follow? → A: JSON object with steps and memory channels arrays.
- Q: How should references behave when agents lack filesystem access? → A: Allow configurable base URL that converts paths into absolute links.
- Q: How should nested file references be handled? → A: Enforce tree-style references with warnings and a max depth.
- Q: How should `id` fields for step metadata be generated? → A: Derive ids from instruction file paths.
- Q: What rate-limit strategy applies to file-first renders? → A: No explicit throttling; callers manage volume.
- Q: What memory/log format should be enforced by default? → A: Library stays agnostic; users reference a folder plus a format descriptor file, with a built-in hierarchical `.md` template available when none is provided.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Render compact root instruction (Priority: P1)

Prompt architects can render any existing blueprint/instruction set in a "file-first" mode that emits a short persona description, the primary objectives, and an ordered task list where every task references a concrete file (e.g., `instructions/think.md`) for details.

**Why this priority**: Without an automated root instruction, engineers must manually prune context, leading to bloated prompts and inconsistent agent guidance.

**Independent Test**: Execute `promptic` preview/SDK render against `examples/us1-blueprints` with the new mode and verify the output only contains summary text plus file references.

**Architecture Impact**: Touches `promptic.blueprints.serialization` (adds render mode), `promptic.pipeline.template_renderer` (injects summary layer), and `promptic.instructions.store` (surface metadata). Respect DIP by keeping render strategy pluggable and injecting dependencies instead of branching in callers.

**Quality Signals**: New unit tests for render strategy, regression coverage in `tests/integration/test_blueprint_preview_sdk.py`, docs_site quickstart update, and `AICODE-NOTE` explaining how file references are generated.

**Acceptance Scenarios**:

1. **Given** a blueprint with multiple step instruction files, **When** the user renders it in file-first mode, **Then** the output lists each step with a short summary and `instructions/<step>.md` reference instead of full text.
2. **Given** the file-first renderer encounters a referenced file that is missing, **When** rendering runs, **Then** it fails fast with a descriptive error indicating which path must be created.

---

### User Story 2 - Guide agents to fetch deep context on demand (Priority: P2)

As an operator running an agent, I can hand the root instruction to the LLM and it will know exactly where to look (specific file paths or memory folders) if additional details are needed for any step.

**Why this priority**: The README emphasizes keeping the LLM context lean while still enabling drill-down, so references must be explicit and reliable.

**Independent Test**: Use `examples/complete/research_flow.yaml` in preview mode, confirm the rendered prompt contains inline cues such as “(see instructions/collect_step.md for full checklist)” for every step.

**Architecture Impact**: Requires `promptic.context.rendering` to annotate steps with stable URIs and `promptic.pipeline.executor` logging to preserve those hints. SOLID impact: introduce a dedicated `ReferenceFormatter` so referencing logic is isolated and mockable.

**Quality Signals**: Contract test in `tests/contract/test_template_context_contract.py` verifying reference schema, plus documentation in `docs_site/context-engineering/blueprint-guide.md`.

**Acceptance Scenarios**:

1. **Given** a rendered output, **When** an agent inspects any step, **Then** it sees both a short summary and explicit reference text describing how to retrieve the detailed file or memory entry.

---

### User Story 3 - Declare memory and metadata instructions centrally (Priority: P3)

Library maintainers define a memory section (e.g., `memory/` folder pointers, formats) and optional clarifications directly within the root instruction so agents know exactly where to write intermediate notes without additional prompt engineering.

**Why this priority**: Shared memory guidance is currently ad-hoc and buried inside deep files; surfacing it centrally prevents lost context and enforces consistent storage formats.

**Independent Test**: Render a blueprint that includes `memory/*.md` guides and verify the root output surfaces “If you need to remember facts, write to memory/log.md using <format>”.

**Architecture Impact**: Uses `promptic.instructions.store` to detect memory guides, extends `promptic.pipeline.builder` to attach metadata, and ensures `promptic.context.template_context` exposes memory descriptors without leaking file IO responsibilities across layers.

**Quality Signals**: Add unit tests for memory descriptor extraction, ensure integration coverage in `tests/integration/test_instruction_templating.py`, and update docs_site memory guidance page.

**Acceptance Scenarios**:

1. **Given** a blueprint that declares memory instructions, **When** it is rendered, **Then** the output includes a dedicated “Memory & logging” block summarizing location, structure, and retention expectations.

---

### Edge Cases

- Missing or unreadable instruction file should halt rendering with actionable diagnostics rather than embedding stale data.
- Blueprints with nested instructions (e.g., instructions referencing other files) must avoid circular references; enforce tree-style references with explicit parent-child relationships, warn on loops, and cap recursion depth (default 3 levels).
- When step summaries exceed the configured max tokens, renderer must truncate gracefully while keeping file reference intact.
- Agents that cannot access filesystem paths rely on references prefixed with a configurable base URL so every pointer becomes an absolute, clickable link.
- Detect when memory/log directories are absent and either omit the block or instruct the user to create the folder before execution; if no custom format descriptor is present, fall back to the built-in hierarchical folder + `.md` template and mention how to override it.
- High-frequency render callers are responsible for applying their own throttling; file-first mode does not introduce additional rate limits beyond existing infrastructure policies.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `file_first` render mode (CLI flag and SDK option) that emits a compact persona, goal, and ordered steps list referencing files instead of inlining their content.
- **FR-002**: System MUST summarize each referenced instruction file to ≤ N tokens (configurable, default 120) and include the file path in the same bullet.
- **FR-003**: System MUST include a “See more” callout per step that makes it explicit how the agent can open the detailed file (e.g., “open instructions/think.md”).
- **FR-004**: System MUST automatically surface memory/logging instructions by scanning `memory/` (or configured directories) and describing write formats and retention hints in the root prompt, pulling details from a user-specified format descriptor file when present and otherwise referencing the built-in hierarchical folder + `.md` template.
- **FR-005**: System MUST validate referenced files/directories up front and fail with a deterministic error message that lists every missing path.
- **FR-006**: System MUST allow blueprint authors to override summary text via front-matter metadata while keeping file references intact.
- **FR-007**: System MUST emit structured metadata (JSON alongside markdown) whose top-level object contains `steps` and `memory_channels` arrays; each step entry includes `{id, title, summary, reference_path, detail_hint, token_estimate}` so downstream tooling can programmatically resolve references, with `id` deterministically derived from the canonical instruction file path (e.g., `instructions_think_md`).
- **FR-008**: System MUST record render metrics (token counts before/after, number of references produced) so reductions in context can be measured in tests.
- **FR-009**: System MUST accept an optional base URL configuration that transforms each file reference into an absolute link while leaving repository-relative paths unchanged when no base is supplied.
- **FR-010**: System MUST model nested references as a tree where each node lists its child references; rendering must warn on cycles and stop traversal once the configurable depth limit (default 3) is exceeded.
- **FR-011**: System MUST expose render metrics so external orchestrators can implement rate limiting if needed, but SHALL NOT enforce an internal throttle specific to file-first mode.

### Key Entities *(include if feature involves data)*

- **PromptHierarchyBlueprint**: Aggregates persona, objectives, ordered steps, memory guides, and associated file references derived from existing blueprint YAML plus filesystem metadata.
- **InstructionReference**: Represents a single step reference with attributes: `title`, `summary`, `path`, `detail_hint`, and `token_estimate`.
- **MemoryChannel**: Describes writable memory/log destinations with attributes: `location`, `expected_format`, `format_descriptor_path`, `retention_policy`, and `usage_examples`; `format_descriptor_path` points to the user-defined format file or is omitted when using the default hierarchical `.md` template.

### Architecture & Quality Constraints *(from Constitution)*

- **AQ-001**: Rendering strategies stay inside `promptic.pipeline.template_renderer`; they accept immutable `PromptHierarchyBlueprint` data produced by domain entities, ensuring dependencies flow inward (Entities → Use Cases → Interface adapters).
- **AQ-002**: Introduce small, single-responsibility classes (e.g., `FileSummaryService`, `ReferenceFormatter`) to prevent god objects; each must be injected to facilitate mocking and adherence to the Dependency Inversion Principle.
- **AQ-003**: Extend unit coverage for blueprint serialization, add integration tests for render pipelines, and ensure contract tests confirm metadata schema; all suites run in CI plus locally via `pytest tests -k file_first`.
- **AQ-004**: Update docs_site quickstart, blueprint guide, and memory instructions to explain the new mode; add `AICODE-NOTE` comments near rendering entry points to indicate file-first behavior.
- **AQ-005**: Cap helper functions to ≤40 lines, enforce descriptive naming (e.g., `build_reference_outline`), and forbid dead-code branches by guarding new behavior behind explicit mode flags.

### Assumptions

- Agents consuming prompts can access the same repository (or synced storage) so filesystem paths resolve without extra translation.
- Blueprint authors will continue to store canonical guidance under `instructions/` and `memory/`, keeping filenames aligned with step identifiers.
- Existing render modes remain available; file-first mode is opt-in to avoid breaking current users.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rendering a sample blueprint in file-first mode reduces tokens sent to the LLM by at least 60% compared to the full inline render while preserving task completeness.
- **SC-002**: 100% of steps in supported blueprints include both a summary and a valid reference path detectable by automated tests.
- **SC-003**: At least 90% of user acceptance tests confirm agents can follow references to fetch deeper context without additional human clarification.
- **SC-004**: Memory/logging guidance is surfaced in every blueprint that defines `memory/` assets, verified by integration tests covering at least two example projects.
- **SC-005**: All related pytest suites (unit, integration, contract) pass locally and in CI with evidence linked in the PR.
- **SC-006**: Relevant docs_site pages, specs, and inline `AICODE-*` notes are updated and reviewed alongside the code change, with documentation PR merged together with the feature.
