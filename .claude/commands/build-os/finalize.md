# Build OS: Finalize Build

You are the Build OS finalizer. Your job is to perform final review, cleanup, and prepare the built application for use.

## Prerequisites Check

1. Load the most recent build state from `agents/*/build_state.json`
2. Verify all milestones are `complete`
3. If any milestones are not complete, report which ones and suggest running `/build-os/resume`

## Steps

### 1. Clean Up Worktrees
Check for any remaining worktrees in `trees/`:
- List all worktrees with `git worktree list`
- Remove any worktrees belonging to this build
- Report any that couldn't be removed

### 2. Run Full Test Suite
Run all tests across the entire project:

**Backend tests:**
```bash
cd output/{product-slug}/app/server
uv run pytest -v
```

**Frontend build:**
```bash
cd output/{product-slug}/app/client
npm run build
```

Report results:
- Total tests run / passed / failed
- Build success/failure

### 3. Run Lint Checks
```bash
# Backend
cd output/{product-slug}/app/server
uv run ruff check .

# Frontend
cd output/{product-slug}/app/client
npx eslint src/ --no-error-on-unmatched-pattern
```

Fix any issues found.

### 4. Generate Project README
Update `output/{product-slug}/README.md` with:
- Product name and description (from product overview)
- Setup instructions (backend + frontend)
- Available API endpoints (list all routes)
- Tech stack summary
- Sections included

### 5. Final Report
Display a summary:

```
Build Complete!
───────────────
Product: {product_name}
Build ID: {build_id}
Output: {output_path}

Milestones: {completed}/{total} complete
Tests: {passed}/{total} passing
Build: ✓ Frontend compiles | ✓ Backend runs

Sections Built:
  ✓ Shell (navigation, routing, layout)
  ✓ Dashboard (frontend + API + wired)
  ✓ Agents (frontend + API + wired)
  ...

Total Cost: ${total_cost}

To start the application:
  cd {output_path}
  ./scripts/start.sh
```

### 6. Update Build State
- Set all milestones to `complete` (should already be)
- Record finalization timestamp
- Save final state

## Output
- Clean project at `output/{product-slug}/`
- All tests passing
- README with setup instructions
- Final build report

## Important Rules
- Auto-proceed through all steps without approval
- If some tests fail, report them but don't block finalization
- Clean up ALL worktrees, even from failed builds
- The README should be comprehensive enough for a new developer to set up the project
