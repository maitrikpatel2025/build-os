# Build OS: One-Shot Build (Full Pipeline)

You are the Build OS orchestrator. Your job is to automatically build the entire application by chaining all commands sequentially — from shell through every section to finalization.

## Prerequisites Check

1. Load the most recent build state from `agents/*/build_state.json`
2. Verify the build has been initialized (build state exists with milestones)
3. If no build state, tell user to run `/build-os/init` first
4. If no scaffold exists (no `output_path`), run the scaffold step first

## Pipeline

Execute these steps in order, skipping any that are already complete:

### Phase 1: Foundation
1. **Scaffold** (if `output_path` not set):
   - Generate the project structure following `/build-os/scaffold` instructions
   - Create all directories, boilerplate, and config files
   - Initialize git

### Phase 2: Shell
2. **Build Shell** (if milestone `01-shell` is not `complete`):
   - Follow `/build-os/build-shell` instructions
   - Implement navigation, routing, layout, design tokens
   - Validate build
   - Mark milestone complete

### Phase 3: Sections (repeat for each section milestone)
For each section milestone in order (02, 03, 04, ...):

3. **Build Section Frontend**:
   - Follow `/build-os/build-section {section-id}` instructions
   - Convert TSX components to JSX
   - Create page component with mock data
   - Validate build

4. **Build Section API**:
   - Follow `/build-os/build-api {section-id}` instructions
   - Generate Pydantic models and FastAPI routes
   - Generate and run tests

5. **Wire Data**:
   - Follow `/build-os/wire-data {section-id}` instructions
   - Replace mock data with API calls
   - Add loading/error states

6. **Validate**:
   - Follow `/build-os/validate {section-id}` instructions
   - Run all tests
   - Merge worktree on success

### Phase 4: Finalization
7. **Finalize**:
   - Follow `/build-os/finalize` instructions
   - Run full test suite
   - Generate documentation
   - Report results

## Progress Reporting
After each milestone completes, report:
- Which milestone just completed
- How many remain
- Any issues encountered

## Error Handling
- If a step fails, attempt to fix and retry once
- If retry fails, pause and report the failure
- The user can then fix manually and run `/build-os/resume` to continue

## Important Rules
- Auto-proceed through ALL steps without asking for approval
- This is the fully automated pipeline — no user interaction until complete or error
- Read instruction files fresh for each step (don't cache)
- Update build state after every significant step
- Commit in worktrees after each sub-step (frontend, backend, wire)
- Track total execution in build state
