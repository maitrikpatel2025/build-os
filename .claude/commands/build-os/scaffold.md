# Build OS: Scaffold Project

You are the Build OS scaffolder. Your job is to generate the full-stack project structure with boilerplate code.

## Prerequisites Check

1. Find the most recent build state in `agents/*/build_state.json`
2. If no build state found, tell user to run `/build-os/init` first and stop
3. Verify the build state has milestones and a product name

## Steps

### 1. Load Build State
Read the build state and extract:
- `product_name` → used for directory naming
- `tech_stack` → determines which boilerplate to generate
- `design_system` → configures Tailwind and fonts
- `milestones` → determines which section directories to create
- `entities` → informs model scaffolding

### 2. Create Project Structure
Create the output project at `output/{product-slug}/` where product-slug is the lowercase, hyphenated product name:

```
output/{product-slug}/
├── app/
│   ├── client/                    # React frontend
│   │   ├── src/
│   │   │   ├── components/        # Shared UI components
│   │   │   ├── sections/          # Per-section pages (empty dirs)
│   │   │   │   ├── dashboard/
│   │   │   │   ├── agents/
│   │   │   │   └── ...
│   │   │   ├── shell/             # App shell (nav, layout)
│   │   │   │   └── AppShell.jsx   # Placeholder shell
│   │   │   ├── api/               # API client services
│   │   │   ├── types/             # Shared type definitions
│   │   │   ├── App.jsx            # Root with React Router
│   │   │   ├── main.jsx           # Entry point
│   │   │   └── index.css          # Tailwind imports
│   │   ├── package.json
│   │   ├── vite.config.js
│   │   ├── tailwind.config.js
│   │   ├── postcss.config.js
│   │   └── index.html
│   │
│   └── server/                    # FastAPI backend
│       ├── server.py              # Entry point with CORS + health check
│       ├── routes/                # Per-section API routes (empty)
│       ├── models/                # Pydantic + DB models (empty)
│       ├── core/                  # Business logic
│       │   └── database.py        # SQLAlchemy setup
│       ├── tests/                 # pytest test files
│       │   └── conftest.py        # Test fixtures
│       └── pyproject.toml         # FastAPI, SQLAlchemy, etc.
│
├── scripts/
│   ├── start.sh                   # Start both services
│   └── stop.sh                    # Stop both services
│
├── .ports.env
├── .env.sample
├── .gitignore
└── README.md
```

### 3. Configure Design System
Using the design system from build state:
- Set Tailwind config colors (primary, secondary, neutral) from the product plan's color palette
- Set font families in Tailwind config
- Add Google Fonts link in index.html
- If `tokens.css` exists in the design system, copy it to the client src

### 4. Configure App.jsx with Routes
Create `App.jsx` with React Router routes for each section from the milestones:
- Import each section's page component (placeholder)
- Add `<Route path="/{section-id}" element={<SectionPage />} />`
- Create placeholder page components for each section

### 5. Configure server.py
Set up the FastAPI server with:
- CORS middleware allowing all origins
- Health check endpoint at `/api/health`
- Comment placeholders for route registration

### 6. Initialize Git
Run `git init` in the output directory and make an initial commit with the scaffold.

### 7. Update Build State
Set `output_path` in the build state to the output directory path and save.

## Output
- Scaffolded project at `output/{product-slug}/`
- Git initialized with initial commit
- Updated build state with output_path

## Next Step
Tell the user: "Run `/build-os/build-shell` to build the application shell."

## Important Rules
- Auto-proceed through all steps without approval
- Use JSX (not TypeScript) for all React components
- Ensure the scaffold compiles: `cd output/{product-slug}/app/client && npm install && npm run build` should succeed
- Never modify product-plan files
- If templates exist in `templates/frontend/` or `templates/backend/`, copy from there first, then customize
