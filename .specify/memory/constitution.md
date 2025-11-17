<!--
Sync Impact Report
- Version: template -> 1.0.0
- Principles Updated:
  - [PRINCIPLE_1_NAME] -> P1. Clean Architecture & SOLID Boundaries
  - [PRINCIPLE_2_NAME] -> P2. Evidence-Driven Testing
  - [PRINCIPLE_3_NAME] -> P3. Automated Quality Gates
  - [PRINCIPLE_4_NAME] -> P4. Documentation & Traceable Collaboration
  - [PRINCIPLE_5_NAME] -> P5. Readability & Developer Experience
- Added Sections: Execution Standards, Development Workflow & Quality Gates
- Templates Updated:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
  - ⚠ .specify/templates/commands/ (directory missing; create guidance when commands are added)
- Follow-ups:
  - TODO(RATIFICATION_HISTORY): Capture prior governance history if legacy guidance resurfaces.
-->
# promptic Constitution

## Core Principles

### P1. Clean Architecture & SOLID Boundaries
- Each feature is designed around clean layers (Entities → Use Cases → Interface/Adapters) with dependencies pointing inward only; frameworks never import domain rules.
- Every module/class MUST declare and honor SOLID responsibilities. When trade-offs occur, document the deviation plus mitigation inside the spec or code via `# AICODE-NOTE`.
- Dependency inversion is enforced through explicit interfaces/protocols so implementations can be swapped without editing calling layers.
_Rationale: Stable, isolated layers keep Telegram-centric automation maintainable as the repo grows._

### P2. Evidence-Driven Testing
- Tests are written or updated before code is accepted; `pytest tests/ -v` MUST pass locally and in CI for every change.
- Each behavior change pairs with unit coverage plus integration/contract tests whenever APIs or adapters are touched.
- Bug fixes include regression tests proving the failure then the resolution.
_Rationale: Tests are the only acceptable proof that telegram note flows and automations keep working._

### P3. Automated Quality Gates
- Black (line-length 100), isort (profile black), and the configured `pre-commit` hooks run before any commit or merge.
- No contributor may claim tooling is unavailable—install the dependencies or fix PATH per AGENTS.md.
- Static checks, linters, and formatters are treated as blocking gates, not suggestions.
_Rationale: Deterministic tooling keeps diffs reviewable and prevents style regressions._

### P4. Documentation & Traceable Collaboration
- `docs_site/`, specs, and plan files are updated alongside code so that architecture, APIs, and operational steps never drift.
- Use `# AICODE-NOTE`, `# AICODE-TODO`, and `# AICODE-ASK` comments to capture AI/user context; resolve `ASK` items before merge and document the answers.
- Every feature spec and plan must describe its tests, architecture boundaries, and quality signals to satisfy reviewers quickly.
_Rationale: Written alignment is the only way to coordinate human + AI contributors asynchronously._

### P5. Readability & Developer Experience
- Prefer small, intention-revealing modules and functions (<100 logical lines) with descriptive names over clever abstractions.
- All public APIs include docstrings that explain side effects, error handling, and contracts; private helpers include inline comments when logic is non-obvious.
- No `.md`/`.txt` status dumps in the repo root—knowledge lives in specs, docs_site, or inline comments where it belongs.
_Rationale: Readable code and docs reduce onboarding friction and prevent hidden tribal knowledge._

## Execution Standards

1. Follow Python 3.x best practices; confirm exact minor version in runtime docs (**TODO(RUNTIME_VERSION): confirm target Python version once packaging is defined**).
2. Source code MUST remain formatted with Black + isort; rerun formatting whenever CI or `pre-commit` flags an issue.
3. Tests use `pytest` and `pytest-asyncio`; integration and contract coverage is mandatory for external boundaries.
4. Documentation updates belong in `docs_site/` plus the relevant spec/plan/task artifacts under `specs/`.
5. Secrets, tokens, or credentials never enter the repo; use environment variables or secret managers only.

## Development Workflow & Quality Gates

1. Kick off `/speckit.plan` to capture research, architecture, and the Constitution Check before coding.
2. Run `/speckit.spec` to author user stories with independent acceptance tests, architecture impact, and documentation scope.
3. Execute `/speckit.tasks` to break work into independently testable slices that include tests and doc updates.
4. Implement features while keeping layers isolated, honoring SOLID, and documenting reasoning via `AICODE` tags.
5. Update docs, run the full pytest suite, then execute `pre-commit run --all-files` before requesting review.
6. Reviewers block merges if any step above lacks evidence or if readability/architecture standards slip.

## Governance

- This constitution supersedes informal guidance. Reviewers enforce it on every PR, and bots may reject work lacking constitution evidence.
- Amendments require: (1) justification documented in `docs_site/architecture/` or the affected spec, (2) consensus among maintainers, (3) version bump logged below.
- Versioning follows semantic rules: MAJOR for breaking/removing principles, MINOR for adding or expanding a principle/section, PATCH for clarifications only.
- Compliance is verified at every release checkpoint; publish deviations plus remediation tasks in `docs_site/development/known-gaps.md`.

**Version**: 1.0.0 | **Ratified**: 2025-11-17 | **Last Amended**: 2025-11-17
