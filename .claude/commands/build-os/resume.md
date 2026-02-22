# Build OS: Resume Build

You are the Build OS resume handler. Your job is to resume a failed or paused build from the last successful point.

## Steps

### 1. Find Build State
Load the most recent build state from `agents/*/build_state.json`.
If no build state found, tell user to run `/build-os/init` first.

### 2. Analyze Current State
Determine where the build left off:
- Check each milestone's status in order
- Find the first milestone that is NOT `complete`
- Determine the sub-step based on its status:
  - `pending` → start from beginning (set up worktree, build frontend)
  - `in_progress` → resume frontend build
  - `frontend_done` → proceed to build API
  - `backend_done` → proceed to wire data
  - `wired` → proceed to validate
  - `tested` → retry validation or complete manually

### 3. Check Worktree State
For the milestone to resume:
- If worktree exists and is valid → use it
- If worktree exists but is corrupted → remove and recreate
- If no worktree → create a new one

### 4. Resume Execution
Based on the sub-step, execute the appropriate command:

| Milestone Status | Resume Action |
|-----------------|---------------|
| `pending` | Run full milestone: frontend → API → wire → validate |
| `in_progress` | Continue frontend build, then API → wire → validate |
| `frontend_done` | Run `/build-os/build-api {section-id}` |
| `backend_done` | Run `/build-os/wire-data {section-id}` |
| `wired` | Run `/build-os/validate {section-id}` |
| `tested` | Retry validation |

For the shell milestone (no section-id):
| `pending` / `in_progress` | Run `/build-os/build-shell` |

### 5. Continue Pipeline
After resuming the current milestone, continue with remaining milestones following the same pattern as `/build-os/build-all`.

### 6. Report
Tell the user:
- Where the build resumed from
- Current progress
- What's running now

## Important Rules
- Auto-proceed through all steps without approval
- Don't rebuild completed milestones
- Preserve any existing work in worktrees
- If a worktree has uncommitted changes, commit them before proceeding
- Handle the edge case where the output project doesn't exist (re-scaffold)
