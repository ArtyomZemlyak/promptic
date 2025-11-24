# Data Model: Prompt Versioning System

**Input**: Feature specification from `/specs/005-prompt-versioning/spec.md`

## Entities

### VersionResolver

**Layer**: Domain (Interface)  
**Location**: `src/promptic/versioning/domain/resolver.py`

Interface for version resolution strategies. Defines the contract for resolving prompt versions from directory paths and version specifications.

**Methods**:
- `resolve_version(path: str, version_spec: VersionSpec) -> str`: Returns the resolved file path for a given path and version specification. Raises `VersionNotFoundError` if version not found.

**VersionSpec Types**:
- `"latest"` (or omitted): Resolve to latest version in directory
- `str` (e.g., `"v1"`, `"v1.0.0"`, `"v1.1"`): Resolve to specific version
- `dict` (hierarchical): Map path patterns to version specifications (e.g., `{"root": "v1", "instructions/process": "v2"}`)

**Relationships**:
- Implemented by `VersionedFileScanner` (adapter)
- Used by `NodeNetworkBuilder` (use case) for version-aware prompt loading
- Used by `VersionExporter` (use case) for resolving versions during export

**Validation Rules**:
- Version specifications must be valid semantic versioning format or "latest"
- Path must be a valid filesystem path (absolute or relative)
- Resolved file path must exist and be readable

**State Transitions**: None (stateless interface)

---

### VersionedFileScanner

**Layer**: Adapter (Implementation)  
**Location**: `src/promptic/versioning/adapters/scanner.py`

Adapter implementation that performs filesystem operations for version detection. Implements `VersionResolver` interface.

**Attributes**:
- `cache: Dict[str, List[VersionInfo]]`: Cache of version listings per directory path
- `cache_timestamps: Dict[str, float]`: Directory modification timestamps for cache invalidation
- `version_pattern: re.Pattern`: Compiled regex pattern for semantic versioning detection

**Methods**:
- `resolve_version(path: str, version_spec: VersionSpec) -> str`: Implements version resolution by scanning directory for versioned files
- `scan_directory(directory: str) -> List[VersionInfo]`: Scans directory for versioned files, returns sorted list
- `extract_version_from_filename(filename: str) -> Optional[SemanticVersion]`: Extracts version identifier from filename using regex patterns
- `normalize_version(version_str: str) -> SemanticVersion`: Normalizes simplified forms (v1 → v1.0.0, v1.1 → v1.1.0)
- `get_latest_version(versions: List[SemanticVersion]) -> SemanticVersion`: Determines latest version using semantic versioning comparison rules

**VersionInfo Structure**:
```python
@dataclass
class VersionInfo:
    filename: str           # Full filename (e.g., "prompt_v1.0.0.md")
    path: str              # Full file path
    base_name: str         # Base name without version (e.g., "prompt.md")
    version: SemanticVersion  # Parsed semantic version
    is_versioned: bool     # True if version detected, False for unversioned fallback
```

**SemanticVersion Structure**:
```python
@dataclass
class SemanticVersion:
    major: int             # Major version number
    minor: int             # Minor version number (0 if not specified)
    patch: int             # Patch version number (0 if not specified)

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: 'SemanticVersion') -> bool:
        # Comparison following semantic versioning rules
        # (major, minor, patch) tuple comparison
```

**Relationships**:
- Implements `VersionResolver` interface
- Uses `SemanticVersion` utility for version parsing and comparison
- Caches version listings to avoid repeated filesystem scans

**Validation Rules**:
- Directory must exist and be readable
- Version detection uses patterns: `_v{N}`, `_v{N}.{N}`, `_v{N}.{N}.{N}`
- Cache invalidated when directory modification time changes

**State Transitions**:
- Cache populated on first directory scan
- Cache invalidated on directory modification time change
- Cache cleared on explicit invalidation

---

### HierarchicalVersionResolver

**Layer**: Domain (Entity)  
**Location**: `src/promptic/versioning/domain/resolver.py`

Domain entity that extends `VersionResolver` to support hierarchical version specifications. Takes a dictionary mapping path patterns to version specifications and applies version resolution recursively when resolving nested prompt references.

**Attributes**:
- `base_resolver: VersionResolver`: Base resolver for single-file version resolution
- `version_map: Dict[str, VersionSpec]`: Hierarchical version specification mapping path patterns to versions

**Methods**:
- `resolve_version(path: str, version_spec: VersionSpec) -> str`: Resolves version using hierarchical specifications, falling back to "latest" for unspecified paths
- `resolve_hierarchical(path: str, version_map: Dict[str, VersionSpec]) -> Dict[str, str]`: Resolves versions for multiple paths using hierarchical specifications

**Relationships**:
- Uses `VersionResolver` interface for base resolution logic
- Used by `NodeNetworkBuilder` when loading prompt hierarchies with version specifications

**Validation Rules**:
- Path patterns must match valid filesystem path format
- Version specifications must be valid (version string or "latest")
- Circular references detected and prevented during hierarchical resolution

**State Transitions**: None (stateless entity)

---

### VersionExporter

**Layer**: Domain (Use Case)  
**Location**: `src/promptic/versioning/domain/exporter.py`

Use case that orchestrates version export operations. Takes a source prompt path, version specification, and target export directory. Resolves the prompt hierarchy at the specified version, discovers all referenced files, and delegates filesystem operations to adapter.

**Attributes**:
- `version_resolver: VersionResolver`: Version resolver for resolving versions during export
- `filesystem_exporter: FileSystemExporter`: Adapter for filesystem operations

**Methods**:
- `export_version(source_path: str, version_spec: VersionSpec, target_dir: str, overwrite: bool = False) -> str`: Exports complete version snapshot, returns root prompt content (with resolved paths). Raises `ExportError` if files missing, `ExportDirectoryExistsError` if target exists without overwrite.
- `discover_referenced_files(prompt_path: str) -> List[str]`: Discovers all files referenced by the prompt hierarchy
- `resolve_export_structure(source_hierarchy: Dict, version_spec: VersionSpec) -> Dict`: Resolves version specifications for all files in hierarchy

**ExportResult Structure**:
```python
@dataclass
class ExportResult:
    root_prompt_content: str    # Root prompt content with resolved paths
    exported_files: List[str]   # List of exported file paths
    structure_preserved: bool   # True if hierarchical structure preserved
```

**Relationships**:
- Depends on `VersionResolver` interface for version resolution
- Depends on `FileSystemExporter` adapter for filesystem operations
- Used by SDK API (`sdk/api.py`) for export functionality

**Validation Rules**:
- Source path must exist and be readable
- Target directory must be writable (or creatable)
- All referenced files must exist (atomic export requirement)
- Export must be atomic (all or nothing)

**State Transitions**:
- Export started: validation of source and target paths
- Export in progress: files discovered and resolved
- Export complete: all files copied, paths resolved
- Export failed: cleanup of partial export, error raised

---

### FileSystemExporter

**Layer**: Adapter (Implementation)  
**Location**: `src/promptic/versioning/adapters/filesystem_exporter.py`

Adapter implementation that handles actual filesystem operations for version exports. Preserves hierarchical directory structure and resolves path references in prompt files.

**Attributes**:
- `base_path: str`: Base path for source prompt hierarchy
- `target_path: str`: Target path for export directory

**Methods**:
- `export_files(source_files: List[str], target_dir: str, preserve_structure: bool = True) -> List[str]`: Copies files from source to target, preserving structure
- `resolve_paths_in_file(file_path: str, path_mapping: Dict[str, str]) -> str`: Resolves path references in file content using path mapping
- `validate_export_target(target_dir: str, overwrite: bool) -> None`: Validates target directory, raises `ExportDirectoryExistsError` if exists without overwrite

**Relationships**:
- Implements export interface defined by `VersionExporter` use case
- Used by `VersionExporter` for filesystem operations

**Validation Rules**:
- Target directory must not exist (unless overwrite=True)
- Source files must exist and be readable
- Target directory must be writable
- Path resolution must maintain relative path relationships

**State Transitions**: None (stateless adapter)

---

### VersionCleanup

**Layer**: Domain (Use Case)  
**Location**: `src/promptic/versioning/domain/cleanup.py`

Use case that orchestrates cleanup operations for exported version directories. Validates that target directories are export directories (not source directories), checks for existing files, and delegates deletion to adapter.

**Attributes**:
- `filesystem_cleanup: FileSystemCleanup`: Adapter for filesystem deletion operations

**Methods**:
- `cleanup_exported_version(export_dir: str, require_confirmation: bool = False) -> None`: Removes exported version directory. Raises `InvalidCleanupTargetError` if target is source directory, `CleanupTargetNotFoundError` if directory doesn't exist.

**Relationships**:
- Depends on `FileSystemCleanup` adapter for filesystem operations
- Used by SDK API (`sdk/api.py`) for cleanup functionality

**Validation Rules**:
- Target directory must be an export directory (heuristic-based detection)
- Source directories must not be deleted (safety check)
- Directory must exist

**State Transitions**:
- Validation started: check if target is export directory
- Validation passed: safe to delete
- Validation failed: error raised, deletion prevented
- Cleanup complete: directory and contents removed

---

### FileSystemCleanup

**Layer**: Adapter (Implementation)  
**Location**: `src/promptic/versioning/adapters/filesystem_cleanup.py`

Adapter implementation that performs safe directory deletion with validation. Validates directory contents to ensure they're export directories, performs recursive deletion of files and subdirectories.

**Attributes**:
- `export_indicators: List[str]`: Patterns indicating export directories (version postfixes in names, metadata files, etc.)

**Methods**:
- `delete_directory(directory: str) -> None`: Recursively deletes directory and all contents. Raises `PermissionError` if deletion fails.
- `validate_export_directory(directory: str) -> bool`: Validates directory is export directory using heuristics. Returns False if uncertain.
- `is_source_directory(directory: str) -> bool`: Checks if directory appears to be a source prompt directory (not export). Returns True if source detected.

**Relationships**:
- Implements cleanup interface defined by `VersionCleanup` use case
- Used by `VersionCleanup` for filesystem operations

**Validation Rules**:
- Directory must exist and be writable
- Export directories must match heuristic patterns
- Source directories must be protected from deletion

**State Transitions**: None (stateless adapter)

---

## Error Types

### VersionNotFoundError
- **When raised**: Requested version doesn't exist in directory
- **Attributes**: `path`, `version_spec`, `available_versions`, `message`
- **Location**: `src/promptic/versioning/domain/errors.py`

### VersionDetectionError
- **When raised**: Ambiguous version detection (multiple patterns match)
- **Attributes**: `filename`, `matched_patterns`, `message`
- **Location**: `src/promptic/versioning/domain/errors.py`

### VersionResolutionCycleError
- **When raised**: Circular version references detected in hierarchical resolution
- **Attributes**: `cycle_path`, `message`
- **Location**: `src/promptic/versioning/domain/errors.py`

### ExportError
- **When raised**: Export operation fails (missing files, permission errors)
- **Attributes**: `source_path`, `missing_files`, `message`
- **Location**: `src/promptic/versioning/domain/errors.py`

### ExportDirectoryExistsError
- **When raised**: Target export directory exists without overwrite flag
- **Attributes**: `target_dir`, `message`
- **Location**: `src/promptic/versioning/domain/errors.py`

### InvalidCleanupTargetError
- **When raised**: Cleanup target is a source directory (not export directory)
- **Attributes**: `target_dir`, `message`
- **Location**: `src/promptic/versioning/domain/errors.py`

### CleanupTargetNotFoundError
- **When raised**: Cleanup target directory doesn't exist
- **Attributes**: `target_dir`, `message`
- **Location**: `src/promptic/versioning/domain/errors.py`

---

## Relationships Summary

```
VersionResolver (interface)
    ↑ implements
VersionedFileScanner (adapter)
    ↑ uses
SemanticVersion (utility)

VersionExporter (use case)
    ↓ depends on
VersionResolver + FileSystemExporter

VersionCleanup (use case)
    ↓ depends on
FileSystemCleanup

NodeNetworkBuilder (existing)
    ↓ extends with
VersionResolver integration

SDK API (existing)
    ↓ adds
Versioning functions (load_with_version, export_version, cleanup_version)
```
