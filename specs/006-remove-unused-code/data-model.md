# Data Model: Remove Unused Code from Library

**Date**: 2025-01-27  
**Feature**: Remove Unused Code from Library

## Overview

This document describes the data model for the simplified promptic library after cleanup. The model focuses on the entities that remain after removing blueprints, adapters, token counting, and related modules.

## Core Entities (KEEP)

### ContextNode

**Location**: `promptic.context.nodes.models.ContextNode`

**Description**: Core entity representing a single file node with content, format, and references. Used by node networks to represent hierarchical file structures.

**Fields**:
- `content`: File content (string)
- `format`: File format (yaml, markdown, json, jinja2)
- `references`: List of references to other nodes
- `metadata`: Optional metadata (dict)

**Relationships**:
- Referenced by: `NodeNetwork.nodes` (many-to-one)
- References: Other `ContextNode` instances via references field

**Validation Rules**:
- Format must be one of: yaml, markdown, json, jinja2
- References must be valid file paths or node IDs
- Content must be valid for the specified format

**State Transitions**: None (immutable after creation)

### NodeNetwork

**Location**: `promptic.context.nodes.models.NodeNetwork`

**Description**: Core entity representing a network of connected nodes. Used to load and render hierarchical file structures.

**Fields**:
- `nodes`: Dictionary of node_id -> ContextNode
- `root_node_id`: ID of the root node
- `metadata`: Optional network metadata (dict)

**Relationships**:
- Contains: Multiple `ContextNode` instances (one-to-many)
- Built by: `NodeNetworkBuilder` (use case)

**Validation Rules**:
- Must have at least one node (root node)
- All references must resolve to existing nodes
- Root node must exist in nodes dictionary

**State Transitions**: None (immutable after creation)

### VersionInfo

**Location**: `promptic.versioning.models.VersionInfo` (if exists)

**Description**: Represents version information for a versioned prompt file.

**Fields**:
- `version`: Semantic version string (e.g., "v1.0.0")
- `file_path`: Path to the versioned file
- `is_latest`: Boolean indicating if this is the latest version

**Relationships**:
- Used by: `VersionResolver` (use case)

**Validation Rules**:
- Version must follow semantic versioning format
- File path must exist

**State Transitions**: None (immutable)

### ExportResult

**Location**: `promptic.versioning.models.ExportResult` (if exists)

**Description**: Result of exporting a versioned prompt structure.

**Fields**:
- `exported_files`: List of exported file paths
- `structure_preserved`: Boolean indicating if directory structure was preserved
- `root_prompt_content`: Content of the root prompt file

**Relationships**:
- Created by: `export_version` function (use case)

**Validation Rules**:
- Exported files must exist
- Root prompt content must be non-empty

**State Transitions**: None (immutable after creation)

## Removed Entities

### ContextBlueprint
**Status**: REMOVED (FR-001)  
**Reason**: Not used in examples 003-006. Replaced by node networks.

### AdapterRegistry
**Status**: REMOVED (FR-002)  
**Reason**: Not used in examples 003-006. Node networks work directly with filesystem.

### TokenCounter
**Status**: REMOVED (FR-003)  
**Reason**: Not used in examples 003-006. Adds unnecessary dependency.

### InstructionNode
**Status**: REMOVED (FR-013)  
**Reason**: Part of instructions package, only used by blueprints.

### NetworkConfig
**Status**: REMOVED (if exists, part of settings)  
**Reason**: Settings package removed (FR-025). Node networks don't need configuration.

## Entity Relationships

```
NodeNetwork
  ├── contains: ContextNode[] (one-to-many)
  └── built by: NodeNetworkBuilder (use case)

ContextNode
  ├── references: ContextNode[] (many-to-many via references)
  └── parsed by: FormatParser (use case)

VersionInfo
  └── resolved by: VersionResolver (use case)

ExportResult
  └── created by: export_version (use case)
```

## Data Flow

### Node Network Loading
1. User calls `load_node_network(root_path)`
2. `NodeNetworkBuilder` reads root file
3. `FormatParser` parses file content
4. `ContextNode` created for root file
5. References resolved recursively
6. `NodeNetwork` created with all nodes
7. Returned to user

### Node Network Rendering
1. User calls `render_node_network(network, target_format, render_mode)`
2. Network traversed starting from root
3. Each node's content converted to target format
4. References resolved and included
5. Final rendered string returned

### Version Loading
1. User calls `load_prompt(prompts_dir, version)`
2. `VersionResolver` finds versioned files
3. File content loaded
4. Returned to user

### Version Export
1. User calls `export_version(source_path, version_spec, target_dir)`
2. `VersionResolver` finds all files for version
3. Files copied to target directory
4. Version suffixes removed from filenames
5. `ExportResult` returned with exported file list

## Validation Rules Summary

- **ContextNode**: Format must be valid, references must resolve
- **NodeNetwork**: Must have root node, all references must resolve
- **VersionInfo**: Version must be valid semantic version
- **ExportResult**: Exported files must exist, root content must be non-empty

## Error Handling

All entities use error classes from `promptic.context.nodes.errors`:
- `NodeNetworkError`: Base error for node network operations
- `NodeNotFoundError`: Node reference cannot be resolved
- `InvalidFormatError`: File format is invalid or unsupported
- `CircularReferenceError`: Circular reference detected in network

Versioning uses error classes from `promptic.versioning.errors` (if exists):
- `VersionNotFoundError`: Requested version does not exist
- `InvalidVersionError`: Version string is invalid

