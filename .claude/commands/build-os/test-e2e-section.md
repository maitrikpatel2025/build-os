# Build OS — Test E2E Section

Run end-to-end browser tests for a section using Playwright MCP. Used by the validator; on failure the validator calls `/resolve_failed_e2e_test` and re-runs this command (max 2 retries).

## Arguments

$ARGUMENTS — first argument: build_id, second argument: section_id

## Instructions

### 1. Load Build State

- Read `agents/{build_id}/build_state.json`
- Extract: output_path, product_plan_path (or product_plan_path from state), e2e_enabled
- If `e2e_enabled` is false, skip e2e tests and return success (JSON status: passed)
- Use working_dir from invocation context (worktree path) for running the app; fall back to output_path if not set

### 2. Check for E2E Test Spec

Check if an e2e test spec already exists:

1. Check `{product_plan_path}/sections/{section_id}/e2e-tests.md` — use if present
2. Check `agents/{build_id}/e2e/{section_id}/test_{section_id}.md` — use if present
3. If neither exists: auto-generate (see step 3)

### 3. Auto-Generate E2E Test Spec (if needed)

Read the section's plan and components to generate a test spec:

- Read section instruction e.g. `product-plan/instructions/incremental/{NN}-{section_id}.md` and `product-plan/sections/{section_id}/README.md`
- Identify user-facing components, routes, and interactions
- If section is API-only (no user-facing UI), skip e2e and return success
- Generate a test spec following the e2e format:

```markdown
# E2E Test: {Section Title}

## User Story
As a user, I want {section_description} so that {value}.

## Test Steps

### Step 1: {Action}
- Navigate to {route}
- **Verify**: {expected behavior}
- **Screenshot**: `01_{descriptive_name}.png`

### Step N: ...

## Success Criteria
- {criterion 1}
- {criterion 2}
```

- Write the generated spec to `agents/{build_id}/e2e/{section_id}/test_{section_id}.md`

### 4. Prepare Application

- Use working_dir (worktree) or output_path as the app root
- Read `.ports.env` from that root if it exists for port configuration
- Start the application (e.g. run `scripts/start.sh` from the app root, or start backend and frontend per project layout)
- Wait for the application to be available
- Determine application URL: http://localhost:${FRONTEND_PORT} from .ports.env, or default http://localhost:3000

### 5. Execute E2E Tests via Playwright MCP

- Use the same pattern as `/test_e2e`: execute browser automation with context_id = build_id, agent_name = e2e_test_runner, e2e_test_file = path to the spec, application_url = from step 4
- Initialize Playwright browser in headed mode
- Navigate to the section's routes and execute each test step from the spec
- For each **Verify** assertion: check the condition and record pass/fail
- For each **Screenshot** directive: capture and save to screenshot directory
- If a step fails, record the error details and continue remaining steps

### 6. Save Screenshots

Save all screenshots to: `agents/{build_id}/e2e/{section_id}/img/`

- Use descriptive filenames matching the spec (e.g. `01_initial_load.png`)
- Ensure directory exists before saving

### 7. Stop Application

- Stop the application processes started in step 4

### 8. Update Build State

- Update the milestone for this section: set `e2e_test_status` = "complete" or "failed", and `e2e_test_results` = the test output JSON
- Save build state

## Report

Return JSON results. Include `test_path` so the validator can pass it to `/resolve_failed_e2e_test` on failure:

```json
{
  "test_name": "E2E: {section_title}",
  "test_path": "<path to the e2e spec file used, e.g. agents/{build_id}/e2e/{section_id}/test_{section_id}.md>",
  "status": "passed|failed",
  "screenshots": [
    "agents/{build_id}/e2e/{section_id}/img/01_screenshot.png"
  ],
  "steps": [
    {
      "step": "Step 1: {description}",
      "passed": true,
      "error": null
    }
  ],
  "error": null
}
```
