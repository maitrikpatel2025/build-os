# Build OS: Build Section Frontend

You are the Build OS section builder. Your job is to build one section's frontend — adapt components, create the page, and wire routing. Run once per section.

**Argument**: `$ARGUMENTS` (the section-id, e.g., `dashboard`, `agents`, `activity`)

## Prerequisites Check

1. Load the most recent build state from `agents/*/build_state.json`
2. Extract the section-id from `$ARGUMENTS`
3. Find the milestone for this section in the milestones list
4. Verify the milestone exists and is `pending` or `in_progress`
5. Verify the shell milestone (`01-shell`) is `complete`
6. If any check fails, report the issue and stop

## Steps

### 1. Set Up Worktree
If the milestone doesn't already have a worktree:
- Create worktree: `trees/{build_id}-{milestone_id}/`
- Branch: `build-{build_id}-{milestone_id}`
- Set up `.ports.env` with allocated ports

### 2. Read Section Specifications
Read these files from the product plan:
- `product-plan/instructions/incremental/{NN}-{section-id}.md` — build instruction
- `product-plan/sections/{section-id}/README.md` — section overview
- `product-plan/sections/{section-id}/components/*.tsx` — reference components
- `product-plan/sections/{section-id}/types.ts` — TypeScript type definitions
- `product-plan/sections/{section-id}/sample-data.json` — mock data

### 3. Convert and Adapt Components
For each component in `product-plan/sections/{section-id}/components/`:

a. **Convert TSX to JSX**:
   - Remove all TypeScript type annotations
   - Remove interface/type declarations
   - Remove generic type parameters
   - Change file extensions from `.tsx` to `.jsx`
   - Keep all React logic, hooks, JSX structure, and styling

b. **Fix imports**:
   - Update import paths to match the output project structure
   - Replace any absolute imports with relative imports
   - Ensure lucide-react icon imports are correct

c. **Place in output project**:
   - Components go in `app/client/src/sections/{section-id}/`

### 4. Create Section Page Component
Create `{SectionName}Page.jsx` in `app/client/src/sections/{section-id}/`:
- Import all section components
- Wire data props from mock data (imported from sample-data.json or inline)
- Wire callback props:
  - Navigation callbacks: `onItemClick → navigate(/{section-id}/{id})`
  - Action callbacks: `onEdit`, `onDelete`, `onCreate` → console.log placeholders
- Handle empty states per instruction spec
- Apply responsive layout

### 5. Wire Routing
In `App.jsx`:
- Import the section page component
- Add/update the route for this section
- Ensure navigation link in shell is active

### 6. Create Mock Data Layer
Create a data file at `app/client/src/sections/{section-id}/data.js`:
- Export sample data from `product-plan/sections/{section-id}/sample-data.json`
- Structure data to match component prop expectations

### 7. Validate
```bash
cd output/{product-slug}/app/client
npm run build
```
- If build fails, fix issues and retry
- Verify the section renders with mock data

### 8. Commit and Update State
- Commit changes: `build-os: implement {section-id} frontend`
- Update milestone status to `frontend_done`
- Save build state

## Output
- Working section with components and mock data
- Milestone status: `frontend_done`

## Next Step
Tell the user: "Run `/build-os/build-api {section-id}` to generate the backend API."

## Important Rules
- Auto-proceed through all steps without approval
- Always convert TSX → JSX
- Follow the instruction file precisely
- Use sample-data.json as the mock data source
- Callback props should use React Router's `useNavigate` where appropriate
- Handle edge cases: empty data, loading states
- Components must be self-contained within the section directory
