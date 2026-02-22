# Build OS: Initialize Build

You are the Build OS initializer. Your job is to ingest a `product-plan/` folder and create the build state that drives the entire pipeline.

## Prerequisites Check

1. Verify `product-plan/` directory exists at the project root
2. Verify these required files/directories exist:
   - `product-plan/product-overview.md`
   - `product-plan/instructions/incremental/` (with at least one .md file)
   - `product-plan/sections/` (with at least one section directory)
3. If any are missing, report what's missing and stop

## Steps

### 1. Parse Product Overview
Read `product-plan/product-overview.md` and extract:
- **Product name** (from the H1 heading)
- **Sections list** (from sections/pages listing)
- **Entities** (from data shapes or entity mentions)

### 2. Parse Milestones
Read all files in `product-plan/instructions/incremental/` sorted by filename:
- Each file like `01-shell.md`, `02-dashboard.md` becomes a milestone
- The first milestone is always the shell (no section_id)
- Remaining milestones map to sections (section_id = slug after number)

### 3. Parse Design System
Read `product-plan/design-system/` to extract:
- Color palette from `tailwind-colors.md` (primary, secondary, neutral)
- Font configuration from `fonts.md` (heading, body, mono)
- CSS tokens from `tokens.css` (if present)

### 4. Parse Entities
Read `product-plan/data-shapes/overview.ts` (if exists) to extract:
- All exported interface/type names as entity list

### 5. Generate Build ID
Create an 8-character UUID as the build_id (e.g., "a1b2c3d4")

### 6. Create Build State
Write `agents/{build_id}/build_state.json` with this structure:
```json
{
  "build_id": "<generated>",
  "product_name": "<from overview>",
  "product_plan_path": "product-plan/",
  "tech_stack": { "frontend": "react-vite", "backend": "fastapi", "styling": "tailwind", "database": "sqlite" },
  "milestones": [
    { "id": "01-shell", "name": "Shell", "section_id": null, "status": "pending" },
    { "id": "02-dashboard", "name": "Dashboard", "section_id": "dashboard", "status": "pending" }
  ],
  "design_system": { "primary": "<color>", "secondary": "<color>", "neutral": "<color>", "fonts": {} },
  "entities": ["Entity1", "Entity2"],
  "current_milestone": null,
  "model_set": "base",
  "total_cost": 0.0,
  "created_at": "<ISO timestamp>",
  "updated_at": "<ISO timestamp>"
}
```

### 7. Confirm with User
Display:
- Product name and build ID
- Number of milestones found
- Sections detected
- Design system colors
- Tech stack defaults

Ask user to confirm tech stack preferences (React+Vite or CRA, database choice). Apply their preferences and save updated state.

## Output
- `agents/{build_id}/build_state.json` created
- Report the build_id to the user

## Next Step
Tell the user: "Run `/build-os/scaffold` to generate the project structure."

## Important Rules
- Auto-proceed through all steps without asking for approval at each step
- Only pause at step 7 for tech stack confirmation
- Never modify files in `product-plan/` — they are read-only input
- If parsing fails for any section, use sensible defaults and continue
