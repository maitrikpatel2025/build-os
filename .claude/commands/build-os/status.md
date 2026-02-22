# Build OS: Check Build Status

You are the Build OS status reporter. Your job is to show the current build progress across all milestones.

## Steps

### 1. Find Build State
Look for build state files in `agents/*/build_state.json`:
- If multiple builds exist, show the most recently updated one
- If no builds exist, tell user to run `/build-os/init` first

### 2. Display Build Info
Show:
- **Build ID**: {build_id}
- **Product**: {product_name}
- **Output**: {output_path}
- **Model Set**: {model_set}
- **Created**: {created_at}
- **Updated**: {updated_at}

### 3. Display Milestone Table
For each milestone, show status with icons:

```
Milestones
──────────
  [x] 01-shell: Shell — complete
  [x] 02-dashboard: Dashboard — complete
  [F] 03-agents: Agents — frontend_done
  [ ] 04-activity: Activity — pending
  [ ] 05-usage: Usage — pending

Progress: 2/5 milestones complete
```

Status icons:
- `[ ]` pending
- `[~]` in_progress
- `[F]` frontend_done
- `[B]` backend_done
- `[W]` wired
- `[T]` tested
- `[x]` complete

### 4. Show Active Worktrees
List any active worktrees in `trees/`:
- Path, branch name, associated milestone

### 5. Show Cost Summary
If cost tracking is available:
- Total accumulated cost
- Per-milestone breakdown (if tracked)

### 6. Show Next Action
Based on current state, suggest the next command to run:
- If scaffold not done: `/build-os/scaffold`
- If shell pending: `/build-os/build-shell`
- If a section is partially done: `/build-os/{next-step} {section-id}`
- If all done: `/build-os/finalize`

## Important Rules
- This is read-only — do not modify any files
- Display information clearly and concisely
- If build state is corrupted, report what's wrong
