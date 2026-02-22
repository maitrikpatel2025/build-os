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

### 1. Read Test Specifications
Read `product-plan/sections/{section-id}/tests.md` for test requirements:
- What user flows should be tested
- What empty states to verify
- What interactions to validate
- What edge cases to cover

### 2. Run Backend Tests
```bash
cd output/{product-slug}/app/server
uv run pytest tests/test_{section_id}.py -v
```
- All API tests must pass
- If tests fail, attempt to fix issues and retry (up to 2 attempts)
- Report test results

### 3. Run Frontend Build Validation
```bash
cd output/{product-slug}/app/client
npm run build
```
- Build must succeed without errors
- If build fails, fix issues and retry

### 4. Run Lint Checks
```bash
# Backend
cd output/{product-slug}/app/server
uv run ruff check .

# Frontend
cd output/{product-slug}/app/client
npx eslint src/sections/{section-id}/ --no-error-on-unmatched-pattern
```
- Fix any lint errors found

### 5. Visual Validation (if Playwright MCP available)
If Playwright MCP is configured:
- Start both services
- Navigate to the section page
- Take a screenshot
- Compare against `product-plan/sections/{section-id}/screenshot.png`
- Report visual differences

If Playwright is NOT available:
- Skip visual validation
- Note it was skipped in the report

### 6. Decision: Pass or Fail

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

### 7. Save Build State
Save the updated state with the validation results.

## Output
- Test results summary
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
