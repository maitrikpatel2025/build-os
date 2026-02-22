# Build OS — Engineering Rules

## What This Is
Build OS consumes a Design OS `product-plan/` and automatically builds a full-stack application using isolated worktrees, composable SDLC workflows, and real-time observability.

## Output Conventions
- **Frontend**: JSX (NOT TypeScript) — convert TSX components from product-plan to JSX during build
- **Backend**: Python with FastAPI — use `uv` for dependency management
- **Styling**: Tailwind CSS with design tokens from product-plan

## Project Structure
- Slash commands: `.claude/commands/build-os/` (11 commands)
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

## Port Allocation
- Backend: 9300-9314 (15 concurrent slots)
- Frontend: 9400-9414 (15 concurrent slots)
- These ranges do NOT overlap with Agent HQ (9100-9214)

## Validation
- Backend: `uv run pytest`, `uv run ruff check .`
- Frontend: `npm run build`, `npx eslint src/`
- No `tsc` — this is a JSX project

## Key Rules
1. Always load build state before any operation
2. Create worktree before modifying output project code
3. Run validation before merging worktree to main
4. Update milestone status after each step completes
5. Convert TSX → JSX when copying components from product-plan
6. Use sample-data.json for mock data, replace with API calls in wire-data step
7. Never modify product-plan files — they are read-only input
