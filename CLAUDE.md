# Build OS — Engineering Rules

## What This Is
Build OS consumes a Design OS `product-plan/` and automatically builds a full-stack application using isolated worktrees, composable SDLC workflows, and real-time observability.

## Output Conventions (default stack)
- **Frontend**: JSX (NOT TypeScript) — convert TSX components from product-plan to JSX during build
- **Backend**: Python with FastAPI — use `uv` for dependency management
- **Styling**: Tailwind CSS with design tokens from product-plan

## Tech Stack — Any Language, Any Framework (build_state.tech_stack)
Build OS supports **any language and framework** via a stack registry and templates.
- **frontend**, **backend**, **styling**, **database** are strings (no fixed enum). Set at init or in build state.
- **Built-in**: frontend `react-vite` | `react-cra`, backend `fastapi`, styling `tailwind`, database `sqlite` | `postgres` | `none`.
- **Custom**: Add `templates/frontend/{id}/` or `templates/backend/{id}/` and use that id (e.g. `next-js`, `vue-vite`, `express`). Optionally register validation commands in `adw_modules/stack_registry.py` (STACK_REGISTRY).
- Scaffolding: custom template dir → built-in generator (react-vite, react-cra, fastapi) → default template → fallback.
- Validation: commands come from the stack registry (`get_validation_commands_for_build(build_id)`); default stacks use pytest/ruff (backend) and npm run build/eslint (frontend).

## Project Structure
- Slash commands: `.claude/commands/build-os/` (12 commands, including test-e2e-section); `.claude/commands/` has test_e2e.md and resolve_failed_e2e_test.md for E2E
- Python modules: `adws/adw_modules/` (10 modules)
- Workflow scripts: `adws/adw_workflows/` (4 orchestration scripts)
- Templates: `templates/frontend/` and `templates/backend/`
- Build state: `agents/{build_id}/build_state.json`
- Worktrees: `trees/{build_id}-{milestone_id}/`
- Output: `output/{product-name}/`

## Build State
- State file: `agents/{build_id}/build_state.json`
- Milestone progression: pending → in_progress → frontend_done → backend_done → wired → tested → complete
- Each milestone gets an isolated git worktree
- Optional: `e2e_enabled` (default true) toggles E2E browser tests during validate. Per-milestone: `e2e_test_status` ("complete" | "failed"), `e2e_test_results` (JSON from test-e2e-section)

## Port Allocation
- Backend: 9300-9314 (15 concurrent slots)
- Frontend: 9400-9414 (15 concurrent slots)
- These ranges do NOT overlap with Agent HQ (9100-9214)

## Validation
- Commands are **stack-dependent**. Use `adw_modules.stack_registry.get_validation_commands_for_build(build_id)` for the current build's tech stack.
- Default (fastapi + react): Backend `uv run pytest`, `uv run ruff check .`; Frontend `npm run build`, `npx eslint src/`.
- No `tsc` for default JSX frontends
- E2E: When `e2e_enabled` and Playwright MCP are available, validate runs `/build-os/test-e2e-section` then `/resolve_failed_e2e_test` on failure (max 2 retries). Specs: `product-plan/sections/{id}/e2e-tests.md` or `agents/{build_id}/e2e/{id}/test_{id}.md`

## Key Rules
1. Always load build state before any operation
2. Create worktree before modifying output project code
3. Run validation before merging worktree to main
4. Update milestone status after each step completes
5. Convert TSX → JSX when copying components from product-plan
6. Use sample-data.json for mock data, replace with API calls in wire-data step
7. Never modify product-plan files — they are read-only input
