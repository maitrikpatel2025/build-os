# Build OS

Automated full-stack application builder that consumes Design OS `product-plan/` exports and produces working React + FastAPI applications.

## Flow

```
Design OS → product-plan/ → Build OS → Working Application
```

## Quick Start

1. **Install dependencies**
   ```bash
   uv sync
   ```

2. **Configure environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your settings
   ```

3. **Copy your product plan**
   ```bash
   cp -r /path/to/design-os/product-plan/ ./product-plan/
   ```

4. **Run Build OS** (CLI mode — step by step)
   ```bash
   # Initialize build from product plan
   /build-os/init

   # Scaffold the project structure
   /build-os/scaffold

   # Build the application shell
   /build-os/build-shell

   # Build each section (repeat for each section)
   /build-os/build-section dashboard
   /build-os/build-api dashboard
   /build-os/wire-data dashboard
   /build-os/validate dashboard

   # Finalize
   /build-os/finalize
   ```

5. **Run Build OS** (One-shot mode)
   ```bash
   /build-os/build-all
   ```

6. **Run Build OS** (SDK orchestration)
   ```bash
   uv run python adws/adw_workflows/build_all.py --build-id <id>
   ```

## Architecture

```
build-os/
├── .claude/commands/build-os/   # 11 slash commands (CLI layer)
├── adws/                        # Orchestration engine (SDK layer)
│   ├── adw_modules/             # Core modules
│   └── adw_workflows/           # Composable workflow scripts
├── templates/                   # Project scaffolding templates
│   ├── frontend/                # React + Vite + Tailwind boilerplate
│   └── backend/                 # FastAPI + SQLAlchemy boilerplate
├── product-plan/                # Input: copied from Design OS export
├── trees/                       # Worktree isolation per milestone
├── agents/                      # Build state + execution logs
└── output/                      # Final built application
```

### Two Layers

- **CLI Layer** (`.claude/commands/build-os/*.md`): 11 sequential slash commands run manually
- **SDK Layer** (`adws/`): Python orchestrator with hooks, logging, cost tracking, and real-time observability

## Slash Commands

| Command | Purpose |
|---------|---------|
| `/build-os/init` | Ingest product-plan and create build state |
| `/build-os/scaffold` | Generate full-stack project structure |
| `/build-os/build-shell` | Build app shell (nav, routing, layout) |
| `/build-os/build-section {id}` | Build one section's frontend |
| `/build-os/build-api {id}` | Generate backend API for a section |
| `/build-os/wire-data {id}` | Connect frontend to backend |
| `/build-os/validate {id}` | Run tests and visual validation |
| `/build-os/build-all` | One-shot: build entire app automatically |
| `/build-os/finalize` | Final review and cleanup |
| `/build-os/status` | Show build progress |
| `/build-os/resume` | Resume from last successful milestone |

## Worktree Strategy

- Each milestone gets its own worktree at `trees/{build_id}-{milestone_id}/`
- Port ranges: Backend 9300-9314, Frontend 9400-9414
- After validation, worktree merges to main and is removed

## Tech Stack (Output)

- **Frontend**: React 18 + Vite + Tailwind CSS + React Router
- **Backend**: FastAPI + SQLAlchemy + Pydantic
- **Styling**: Design tokens from product-plan design system
