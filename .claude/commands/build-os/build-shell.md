# Build OS: Build Application Shell

You are the Build OS shell builder. Your job is to implement the app shell — navigation, routing, layout, and design tokens — in an isolated worktree.

## Prerequisites Check

1. Load the most recent build state from `agents/*/build_state.json`
2. Verify scaffold exists at the `output_path` in build state
3. Verify milestone `01-shell` exists and is `pending`
4. If any check fails, report the issue and stop

## Steps

### 1. Create Worktree
Create an isolated worktree for the shell milestone:
- Path: `trees/{build_id}-01-shell/`
- Branch: `build-{build_id}-01-shell`
- Copy the output project into the worktree (or work directly in output if no git worktree support)

### 2. Read Shell Specifications
Read these files from the product plan:
- `product-plan/instructions/incremental/01-shell.md` — the build instruction
- `product-plan/shell/README.md` — shell component specs
- `product-plan/shell/components/*.tsx` — reference shell components
- `product-plan/design-system/tokens.css` — CSS custom properties
- `product-plan/design-system/tailwind-colors.md` — color configuration
- `product-plan/design-system/fonts.md` — font configuration

### 3. Implement Shell Components
Following the instruction from `01-shell.md`:

a. **Convert TSX to JSX**: Take the reference components from `product-plan/shell/components/` and convert them:
   - Remove all TypeScript type annotations (`: string`, `: Props`, `<T>`, etc.)
   - Remove interface/type declarations
   - Change `.tsx` extensions to `.jsx`
   - Keep all React logic, hooks, and JSX intact

b. **Implement AppShell.jsx** in `app/client/src/shell/`:
   - Responsive sidebar navigation with collapsible mobile menu
   - Header bar with app title
   - Main content area
   - Apply design tokens (colors, fonts)

c. **Implement MainNav.jsx** in `app/client/src/shell/`:
   - Navigation links for all sections from the roadmap
   - Active route highlighting using React Router's `useLocation`
   - Icons from lucide-react for each nav item

### 4. Configure Design Tokens
- Set CSS custom properties from `tokens.css` in `index.css`
- Configure Tailwind colors from the design system
- Add Google Fonts import in `index.html` for all specified fonts
- Ensure font-family references in components match Tailwind config

### 5. Wire Up Routing
In `App.jsx`:
- Import the shell components
- Wrap routes in `<AppShell>`
- Ensure all section routes from milestones have placeholder pages
- Set up a default route (redirect to dashboard or first section)

### 6. Validate
Run validation in the output project:
```bash
cd output/{product-slug}/app/client
npm install
npm run build
```
- If build fails, fix the issues and retry
- Verify the shell renders correctly

### 7. Commit and Update State
- Commit all changes in the worktree: `build-os: implement app shell`
- Update milestone `01-shell` status to `complete`
- Save build state

## Output
- Working app shell with navigation, routing, and design tokens
- Milestone `01-shell` marked complete

## Next Step
Tell the user: "Run `/build-os/build-section dashboard` to build the first section."

## Important Rules
- Auto-proceed through all steps without approval
- Always convert TSX → JSX (remove all TypeScript)
- Follow the instruction file precisely for layout and component structure
- Design tokens must match the product plan exactly
- If a component reference is unclear, implement a reasonable default
- The shell must be responsive (mobile + desktop)
