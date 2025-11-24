# Get Started Examples

These examples are designed for beginners who want to quickly understand how to use promptic for loading and rendering file networks with cross-references.

## Examples

### 1. Inline Full Render (`1-inline-full-render/`)

The simplest example demonstrating full render mode where all references are inlined into a single output.

**What you'll learn:**
- How to load a markdown file with references to other files
- How to render in full mode (inlining all referenced content)
- Minimal setup (just 3 files and ~30 lines of code)

**Files:**
- `main.md` - Main markdown file that includes another file
- `greeting.md` - Included markdown file
- `render.py` - Python script that renders the main file

**Run it:**
```bash
cd examples/get_started/1-inline-full-render
python render.py
```

---

### 2. File First (`2-file-first/`)

Shows how to use file-first rendering mode where file references are preserved as links.

**What you'll learn:**
- How to render in file-first mode (preserving links instead of inlining)
- The difference between file-first and full render modes

**Files:**
- `main.md` - Main markdown file
- `greeting.md` - Referenced markdown file
- `render.py` - Python script demonstrating file-first mode

**Run it:**
```bash
cd examples/get_started/2-file-first
python render.py
```

---

### 3. Multiple Files (`3-multiple-files/`)

Demonstrates rendering multiple root files that share common includes.

**What you'll learn:**
- How to render different root files
- How shared includes work across multiple root files
- How specific includes work for individual files

**Files:**
- `root-1.md` - First root file
- `root-2.md` - Second root file  
- `common.md` - Shared by both root files
- `specific-2.md` - Used only by root-2.md
- `render.py` - Renders both root files

**Run it:**
```bash
cd examples/get_started/3-multiple-files
python render.py
```

---

### 4. File Formats (`4-file-formats/`)

Demonstrates working with multiple file formats (YAML, JSON, Jinja2, Markdown) and converting between them.

**What you'll learn:**
- How to create chains of files in different formats
- How each format references other files
- How to render to different target formats (YAML, JSON, Markdown)
- How markdown rendering wraps structured formats in code blocks

**Files:**
- `root.yaml` - Root YAML file (references file.json)
- `file.json` - JSON file (references file.jinja2)
- `file.jinja2` - Jinja2 template (references file.md)
- `file.md` - Final markdown file
- `render.py` - Renders to all target formats

**Run it:**
```bash
cd examples/get_started/4-file-formats
python render.py
```

---

### 5. Versioning (`5-versioning/`)

Demonstrates how to load specific versions of prompts with hierarchical directory structure and semantic versioning.

**What you'll learn:**
- How to version prompt files using semantic versioning (v1.0.0, v2.0.0, etc.)
- How to load specific versions or the latest version
- How version resolution works in hierarchical structures
- How referenced files are automatically resolved to matching versions

**Files:**
- `prompts/main_v1.0.0.md` and `main_v2.0.0.md` - Versioned main prompts
- `prompts/instructions/process_v1.0.0.md` and `process_v2.0.0.md` - Versioned instructions
- `prompts/context/details_v1.0.0.md` and `details_v2.0.0.md` - Versioned context
- `render.py` - Loads and displays different versions

**Run it:**
```bash
cd examples/get_started/5-versioning
python3 render.py
```

---

### 6. Version Export (`6-version-export/`)

Demonstrates how to export specific versions of prompts, preserving directory structure and removing version suffixes.

**What you'll learn:**
- How to export complete version snapshots
- How exported files maintain directory hierarchy
- How version suffixes are removed from exported filenames
- How path references are resolved in exported structure
- How to compare and deploy different versions

**Files:**
- `prompts/workflow_v1.0.0.md` and `workflow_v2.0.0.md` - Versioned workflows
- `prompts/tasks/`, `steps/`, `output/`, `quality/` - Hierarchical versioned files
- `export_demo.py` - Exports different versions and shows comparison

**Run it:**
```bash
cd examples/get_started/6-version-export
python3 export_demo.py
```

---

## Next Steps

After completing these examples, check out:
- **Advanced Examples** (`../advanced/`) - Real-world examples with multi-agent setups and complex workflows
- **Versioning Examples** (`../versioning/`) - More advanced versioning patterns and use cases
