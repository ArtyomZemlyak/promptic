# Research: Unified Context Node Architecture

## Format Parser Architecture & Registry

- **Decision**: Implement pluggable format parser registry (`FormatParserRegistry`) with interface-based parsers for YAML, Jinja2, Markdown, and JSON. Each parser implements `FormatParser` interface with three methods: `detect()` (identifies format from file/content), `parse()` (extracts structured content), and `to_json()` (converts to canonical JSON representation). Format detection uses file extension as primary signal, with content-based detection (magic bytes, structure analysis) as fallback. Parsers recognize format-specific reference syntax (YAML `$ref:`, Markdown links, JSON objects, Jinja2 variables) and convert to canonical structured format during JSON conversion.
- **Rationale**: Pluggable architecture enables extensibility (custom format parsers) without modifying core code, satisfying OCP. Interface-based design ensures all parsers are substitutable (LSP). JSON as canonical format provides uniform processing regardless of source format, enabling format-agnostic network building. Format-specific reference syntax preserves native authoring experience while enabling unified reference resolution.
- **Alternatives considered**:
  - Single monolithic parser: violates SRP, harder to extend, couples format logic to core system.
  - Format-specific classes without interface: breaks LSP, makes testing and extension difficult.
  - No JSON conversion: requires format-specific processing throughout system, increases complexity.

## Reference Resolution Strategy

- **Decision**: Implement `NodeReferenceResolver` interface with filesystem-based implementation (`FilesystemReferenceResolver`) as default. References support both file paths (primary for filesystem nodes) and generated IDs (for in-memory/programmatic nodes). Path resolution defaults to relative (from referencing node's directory) with absolute path support from configured root. Reference syntax is format-specific (YAML `$ref:`, Markdown `[label](path)`, JSON structured objects, Jinja2 variables/comments) but converts to canonical structured format during parsing.
- **Rationale**: Interface-based resolver enables pluggable resolution strategies (filesystem, URIs, node IDs) without hardcoding assumptions, satisfying DIP. Relative path resolution matches filesystem conventions and enables portable node networks. Absolute path support provides explicit control when needed. Format-specific syntax preserves native authoring while canonical format enables unified processing.
- **Alternatives considered**:
  - Only absolute paths: breaks portability, harder to author and maintain node networks.
  - Only relative paths: limits flexibility for complex scenarios with multiple roots.
  - Single reference syntax across formats: breaks native authoring experience, increases learning curve.

## Cycle Detection & Depth Limiting

- **Decision**: Implement cycle detection using depth-first search (DFS) with visited set during network building. Depth limit (default 10 levels) enforced to prevent stack overflow from extremely deep but valid trees. Cycle detection raises `NodeNetworkValidationError` with full cycle path (e.g., "A → B → C → A") for debugging. Depth limit raises `NodeNetworkDepthExceededError` when exceeded. Both limits configurable per network load operation.
- **Rationale**: Cycle detection prevents infinite recursion bugs and provides actionable error messages. Depth limiting prevents stack overflow while allowing legitimate deep hierarchies. Configurable limits enable different use cases (simple 2-level vs. complex multi-level networks). DFS algorithm is efficient and provides clear cycle paths for debugging.
- **Alternatives considered**:
  - No cycle detection: allows infinite recursion bugs, breaks network building.
  - Fixed depth limit: too rigid, doesn't accommodate different use cases.
  - Breadth-first search: less efficient for cycle detection, doesn't provide clear cycle paths.

## Resource Limits & Token Counting

- **Decision**: Enforce configurable resource limits: max node size (default 10MB per node), max network size (default 1000 nodes), max tokens per node, and max tokens per network. Token counting uses tiktoken library with configurable model specification (default model, e.g., GPT-4). Token counting performed on final rendered content (after all format conversions) to accurately reflect LLM context usage. Model for token counting configurable at network load operation level. All limits configurable per network load operation. When limits exceeded, raise `NodeResourceLimitExceededError` with details about which limit violated and current vs. maximum values.
- **Rationale**: Resource limits prevent context overflow and memory issues, critical for LLM integration. Token limits are the primary constraint for LLM context management. Token counting on final rendered content accurately reflects actual LLM usage. Configurable limits enable different use cases (simple previews vs. complex production networks). Tiktoken provides accurate, model-specific token counting. Model configurability enables different models for different use cases (GPT-4 vs. GPT-3.5-turbo).
- **Alternatives considered**:
  - No resource limits: allows context overflow, breaks LLM integration, causes memory issues.
  - Fixed limits: too rigid, doesn't accommodate different use cases.
  - Character-based limits: inaccurate for LLM context management, doesn't reflect actual token usage.
  - Single model for token counting: doesn't accommodate different LLM models and use cases.

## Schema Validation Strategy

- **Decision**: Attempt schema validation where applicable (based on format, semantic_type metadata, or explicit schema declaration). If no schema applies or validation fails, store content as free-form JSON without structural constraints. Schema validation is optional and non-blocking—nodes with unvalidated or free-form content remain fully functional. Validation errors logged as warnings but do not block node loading or network construction.
- **Rationale**: Schema validation provides structure guarantees when applicable (e.g., blueprint schemas, instruction templates) but doesn't restrict flexibility for free-form content (e.g., arbitrary data nodes, custom memory formats). Non-blocking validation enables graceful degradation and doesn't break existing workflows. Free-form fallback ensures nodes remain functional even when schemas don't apply.
- **Alternatives considered**:
  - Mandatory schema validation: too rigid, breaks flexibility, prevents free-form content.
  - No schema validation: loses structure guarantees, harder to validate blueprint/instruction schemas.
  - Blocking validation: breaks existing workflows, prevents graceful degradation.

## Backward Compatibility Strategy

- **Decision**: Implement adapter layer (`LegacyBlueprintAdapter`, `LegacyInstructionAdapter`) that maps existing `ContextBlueprint`/`InstructionNode` models to `ContextNode` networks. Adapters provide transparent conversion so existing code continues to work without modifications. Migration path documented with tooling for converting existing blueprints/instructions to unified node format. Adapters use adapter pattern to maintain backward compatibility while enabling new unified architecture.
- **Rationale**: Backward compatibility enables incremental migration and reduces risk of breaking existing code. Adapter pattern maintains separation between old and new architectures, satisfying SRP. Transparent conversion ensures existing APIs continue to work. Migration path enables gradual adoption of unified architecture.
- **Alternatives considered**:
  - Breaking changes: high risk, requires rewriting all existing code, breaks existing workflows.
  - Modifying existing models: mixes old and new architectures, violates SRP, harder to maintain.
  - No migration path: prevents adoption, leaves users with incompatible systems.

## Node Identity & Reference Scheme

- **Decision**: Filesystem nodes identified by file path (e.g., `instructions/think.md`) as primary identifier. In-memory/programmatic nodes use generated UUIDs. References can use either path or ID depending on node source. Path-based identity enables filesystem integration and Git-friendly workflows. UUID-based identity enables programmatic node creation and in-memory networks.
- **Rationale**: Path-based identity matches filesystem conventions and enables intuitive reference resolution. UUID-based identity enables programmatic creation without filesystem dependencies. Dual identity scheme accommodates both filesystem and programmatic use cases.
- **Alternatives considered**:
  - Only paths: breaks programmatic creation, doesn't support in-memory networks.
  - Only UUIDs: breaks filesystem integration, harder to author and maintain node networks.
  - Custom ID scheme: adds complexity, doesn't match filesystem conventions.

## Format-Specific Reference Syntax

- **Decision**: Each format uses native reference syntax: YAML uses `$ref:` syntax (e.g., `$ref: instructions/think.md`), Markdown uses link syntax `[label](path)` (e.g., `[See instructions](instructions/think.md)`), JSON uses structured reference objects (e.g., `{"type": "reference", "path": "instructions/think.md"}`), Jinja2 uses template variables or comments. Each format parser recognizes its native reference syntax and converts to canonical structured format during JSON conversion.
- **Rationale**: Native syntax preserves authoring experience and matches format conventions. Users can use familiar syntax for each format without learning new reference schemes. Canonical format enables unified reference resolution regardless of source format.
- **Alternatives considered**:
  - Single reference syntax across formats: breaks native authoring experience, increases learning curve.
  - No reference syntax: requires manual reference management, breaks composition.
  - Format-agnostic syntax: doesn't match format conventions, harder to author.

## Recursive Network Scope

- **Decision**: Support recursive node networks with configurable depth limits (default 10 levels). Recursive networks necessary for complex scenarios with deep nesting (3+ levels) and multi-level cross-referencing. Simple file-first hierarchies (flat or 2-level structures) may not require full recursive network support but architecture supports both from the start.
- **Rationale**: Recursive networks enable flexible composition and solve real-world problems (e.g., instruction → data → memory → another instruction). Architecture must support both simple and complex use cases from the start. Configurable depth limits prevent stack overflow while allowing legitimate deep hierarchies.
- **Alternatives considered**:
  - No recursion: breaks flexible composition, doesn't solve multi-level cross-referencing problems.
  - Fixed recursion depth: too rigid, doesn't accommodate different use cases.
  - Only simple hierarchies: doesn't solve complex scenarios, limits architecture flexibility.

## Token Counting Implementation

- **Decision**: Use tiktoken library with configurable model specification (default model, e.g., GPT-4). Token counting performed on final rendered content (after all format conversions) to accurately reflect LLM context usage. Model for token counting configurable at network load operation level, enabling different models for different use cases. Token counting uses `TokenCounter` interface with tiktoken-based implementation, allowing model-specific token counting.
- **Rationale**: Tiktoken provides accurate, model-specific token counting essential for LLM context management. Counting on final rendered content accurately reflects actual LLM usage. Model configurability enables different models for different use cases (GPT-4 vs. GPT-3.5-turbo). Interface-based design enables pluggable token counting strategies if needed.
- **Alternatives considered**:
  - Character-based estimation: inaccurate for LLM context management, doesn't reflect actual token usage.
  - Single model: doesn't accommodate different LLM models and use cases.
  - Counting on source content: inaccurate, doesn't reflect final rendered content sent to LLM.
  - No token counting: breaks LLM context management, allows context overflow.
