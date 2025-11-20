# Research Findings – File-First Prompt Hierarchy

All critical unknowns identified during specification review were resolved through targeted research and alignment with existing Promptic conventions. Findings below capture the final decisions, rationale, and alternatives considered.

## Metadata Envelope & JSON Structure
- **Decision**: Emit a JSON object containing `steps` and `memory_channels` arrays, where each step entry holds `{id, title, summary, reference_path, detail_hint, token_estimate}` and each memory channel documents `{location, expected_format, format_descriptor_path, retention_policy, usage_examples}`.
- **Rationale**: Aligns with existing SDK expectations for stable, typed payloads while remaining language-agnostic and easy to extend with additional metadata.
- **Alternatives considered**: *(a)* Flat resource arrays that multiplexed steps and memory (rejected: difficult for downstream tooling to filter). *(b)* Map keyed by file path (rejected: brittle when files move or are aliased). *(c)* Embedding metadata solely in markdown (rejected: parsing burden for downstream automations).

## Reference Linking & Base URL Handling
- **Decision**: Keep repository-relative paths in markdown but allow renderers to accept an optional `base_url` parameter that converts every reference into an absolute link for agents without filesystem access.
- **Rationale**: Preserves compatibility with local workflows while enabling hosted documentation portals or remote sandboxes to dereference instructions instantly.
- **Alternatives considered**: *(a)* Fully inlined instruction excerpts (rejected: defeats token-reduction goal). *(b)* Mandatory remote URL structure (rejected: some teams operate air-gapped). *(c)* Opaque resolver IDs (rejected: requires additional orchestration services that do not exist yet).

## Memory Guidance Format
- **Decision**: Keep memory/log formats user-defined via a `format_descriptor_path`; if none is provided, fall back to the built-in hierarchical folders + `.md` template that ships with Promptic examples.
- **Rationale**: Gives teams flexibility to codify bespoke memory shapes (JSONL, CSV, etc.) without forcing format migrations, while still guaranteeing a documented default for quick starts.
- **Alternatives considered**: *(a)* Enforcing append-only plain text logs (rejected: insufficient for teams needing structured data). *(b)* Auto-generating schemas based on detected files (rejected: would guess incorrectly and hide intent). *(c)* Leaving format unspecified (rejected: agents need clear write instructions).

## Rate Limiting & Observability
- **Decision**: File-first mode will not introduce internal throttling; instead it surfaces detailed render metrics (token deltas, reference counts, missing files) so orchestrators can implement their own rate controls.
- **Rationale**: Keeps the library lightweight, avoids surprising behavior differences between render modes, and leverages existing platform-level rate limiting in agent runners.
- **Alternatives considered**: *(a)* Hard-coded per-minute limits (rejected: conflicting deployment needs). *(b)* Separate queues per blueprint (rejected: unnecessary complexity for a rendering library). *(c)* Silent best-effort logging (rejected: insufficient data for capacity planning).
