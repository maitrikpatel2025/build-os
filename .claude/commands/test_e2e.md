# E2E Test Runner

Execute end-to-end (E2E) tests using Playwright browser automation (MCP Server). If any errors occur and assertions fail mark the test as failed and explain exactly what went wrong.

## Variables

context_id: First argument — in Build OS use build_id; in Agent HQ use adw_id
agent_name: Second argument if provided, otherwise use 'e2e_test_runner'
e2e_test_file: Path to the E2E test spec file (e.g. agents/{build_id}/e2e/{section_id}/test_{section_id}.md)
application_url: Optional; if not provided, determine from port configuration:
  - If `.ports.env` exists in working directory, source it and use http://localhost:${FRONTEND_PORT}
  - Otherwise use default http://localhost:3000

## Instructions

- If `application_url` was not provided, check for `.ports.env` in the working directory:
  - If it exists, source it and use http://localhost:${FRONTEND_PORT}
  - Otherwise use default http://localhost:3000
- Read the `e2e_test_file`
- Digest the `User Story` to first understand what we're validating
- IMPORTANT: Execute the `Test Steps` detailed in the `e2e_test_file` using Playwright browser automation
- Review the `Success Criteria` and if any of them fail, mark the test as failed and explain exactly what went wrong
- Review the steps that say '**Verify**...' and if they fail, mark the test as failed and explain exactly what went wrong
- Capture screenshots as specified
- IMPORTANT: Return results in the format requested by the `Output Format`
- Initialize Playwright browser in headed mode for visibility
- Use the determined `application_url`
- Allow time for async operations and element visibility
- IMPORTANT: After taking each screenshot, save it to `Screenshot Directory` with descriptive names. Use absolute paths to move the files to the `Screenshot Directory` with the correct name.
- Capture and report any errors encountered
- Ultra think about the `Test Steps` and execute them in order
- If you encounter an error, mark the test as failed immediately and explain exactly what went wrong and on what step it occurred. For example: '(Step 1 ❌) Failed to find element with selector "query-input" on page "http://localhost:3000"'
- Use `pwd` or equivalent to get the absolute path to the codebase for writing and displaying the correct paths to the screenshots

## Setup

If `.claude/commands/prepare_app.md` exists, read and execute it to prepare the application. Otherwise the caller (e.g. `/build-os/test-e2e-section`) is responsible for having the application running before invoking this command.

## Screenshot Directory

<absolute path to codebase>/agents/<context_id>/<agent_name>/img/<directory name based on test file name>/*.png

Each screenshot should be saved with a descriptive name that reflects what is being captured. The directory structure ensures that:
- Screenshots are organized by context (build_id in Build OS, adw_id in Agent HQ)
- They are stored under the specified agent name
- Each test has its own subdirectory based on the test file name (e.g. test_dashboard → dashboard/, test_application_shell → application_shell/)

## Report

- Exclusively return the JSON output as specified in the test file (and include `test_path` for resolution)
- Capture any unexpected errors
- IMPORTANT: Ensure all screenshots are saved in the `Screenshot Directory`

### Output Format

```json
{
  "test_name": "Test Name Here",
  "test_path": "<absolute or relative path to the e2e test spec file used>",
  "status": "passed|failed",
  "screenshots": [
    "<absolute path to codebase>/agents/<context_id>/<agent_name>/img/<test name>/01_<descriptive name>.png",
    "<absolute path to codebase>/agents/<context_id>/<agent_name>/img/<test name>/02_<descriptive name>.png"
  ],
  "error": null
}
```
