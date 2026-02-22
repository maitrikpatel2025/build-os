# Build OS: Validate Section

You are the Build OS validator. Your job is to run tests and visual validation for one section, then merge the worktree on success.

**Argument**: `$ARGUMENTS` (the section-id, e.g., `dashboard`, `agents`, `activity`)

## Prerequisites Check

1. Load the most recent build state from `agents/*/build_state.json`
2. Extract the section-id from `$ARGUMENTS`
3. Find the milestone for this section
4. Verify milestone status is `wired` (frontend + backend + wiring must be complete)
5. If check fails, report the issue and stop

## Steps

**Stack-aware validation:** Build OS supports any language/framework. Validation commands depend on `build_state.tech_stack`. For built-in stacks (react-vite, react-cra, fastapi) use the commands below. For custom stacks (e.g. next-js, express), run the steps returned by the stack registry: from project root, `uv run python -c "from adws.adw_modules.stack_registry import get_validation_commands_for_build; from adws.adw_modules.build_state import BuildState; s=BuildState.find_latest(); print(get_validation_commands_for_build(s.build_id) if s else [])"` — then run each step's `command` from the output project with `cwd` set to the step's `cwd` relative to output path.

### 1. Read Test Specifications
Read `product-plan/sections/{section-id}/tests.md` for test requirements:
- What user flows should be tested
- What empty states to verify
- What interactions to validate
- What edge cases to cover

### 2. Run Backend Tests
Use the backend validation steps from the stack registry for this build's `tech_stack.backend`, or for default (fastapi):
```bash
cd output/{product-slug}/app/server
uv run pytest tests/test_{section_id}.py -v
```
- All API tests must pass
- If tests fail, attempt to fix issues and retry (up to 2 attempts)
- Report test results

### 3. Run Frontend Build Validation
Use the frontend validation steps from the stack registry for this build's `tech_stack.frontend`, or for default (react-vite/react-cra):
```bash
cd output/{product-slug}/app/client
npm run build
```
- Build must succeed without errors
- If build fails, fix issues and retry

### 4. Run Lint Checks
Use lint steps from the stack registry, or for default stacks:
```bash
# Backend
cd output/{product-slug}/app/server
uv run ruff check .

# Frontend
cd output/{product-slug}/app/client
npx eslint src/sections/{section-id}/ --no-error-on-unmatched-pattern
```
- Fix any lint errors found

### 5. E2E Browser Tests (if enabled and Playwright MCP available)

- From build state, get build_id and e2e_enabled (if missing, treat as true).
- If e2e_enabled is false, skip this step and note in report.
- If Playwright MCP is not configured, skip this step and note in report.
- Otherwise:
  - Run `/build-os/test-e2e-section {build_id} {section-id}` with working_dir set to the worktree path for this milestone (so the app runs from the worktree).
  - If the returned JSON has status "failed":
    - Run `/resolve_failed_e2e_test` with the full failure JSON (include test_path) as $ARGUMENTS. The resolver runs in the same worktree and fixes the code, then re-runs the same e2e test.
    - Re-run `/build-os/test-e2e-section {build_id} {section-id}`. If still failed, repeat resolve + re-run once more (max 2 resolution attempts).
  - If e2e still failed after retries: treat as validation failure (report and do not merge).
  - Update the milestone with e2e_test_status and e2e_test_results from the last test run; save build state.

### 6. Visual Validation (if Playwright MCP available)
If Playwright MCP is configured:
- Start both services
- Navigate to the section page
- Take a screenshot
- Compare against `product-plan/sections/{section-id}/screenshot.png`
- Report visual differences

If Playwright is NOT available:
- Skip visual validation
- Note it was skipped in the report

### 7. Decision: Pass or Fail

**If all tests pass:**
- Commit remaining changes: `build-os: validate {section-id} — all tests pass`
- Merge the worktree branch to main
- Remove the worktree
- Update milestone status to `complete`

**If tests fail after retries:**
- Report which tests failed and why
- Keep the worktree intact for manual fixes
- Update milestone status to `tested` (partial)
- Tell user what needs to be fixed

### 8. Save Build State
Save the updated state with the validation results.

## Output
- Test results summary (unit, e2e, lint)
- E2E status and screenshots path when run (e.g. agents/{build_id}/e2e/{section-id}/)
- Visual comparison (if available)
- Milestone status: `complete` (pass) or `tested` (fail with details)
- Worktree merged and removed on success

## Next Step
If there are more sections to build:
  "Run `/build-os/build-section {next-section-id}` to build the next section."
If all sections are complete:
  "Run `/build-os/finalize` to finalize the build."

## Important Rules
- Auto-proceed through all steps without approval
- All backend tests must pass for validation to succeed
- Frontend must compile without errors
- Fix lint issues automatically where possible
- Keep worktree on failure for debugging
- Report a clear summary of what passed and what failed
