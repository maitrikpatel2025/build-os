"""Milestone coordination operations for Build OS.

Coordinates the per-milestone build lifecycle:
frontend build → backend build → wire data → validate.
Handles worktree creation/cleanup and state transitions.
"""

import logging
import os
from typing import Optional, Tuple

from .build_state import BuildState
from .data_types import MilestoneStatus
from .git_ops import (
    commit_changes,
    make_milestone_branch_name,
    merge_branch_to_main,
)
from .worktree_ops import (
    create_worktree,
    find_available_ports,
    remove_worktree,
    setup_worktree_environment,
)


def setup_milestone(
    state: BuildState, milestone_id: str, logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Set up a milestone for building: create worktree, allocate ports, update state.

    Args:
        state: Current build state
        milestone_id: The milestone ID to set up
        logger: Logger instance

    Returns:
        Tuple of (worktree_path, error_message)
    """
    build_id = state.build_id
    milestone = state.get_milestone(milestone_id)

    if not milestone:
        return None, f"Milestone {milestone_id} not found in build state"

    # Generate branch name
    branch_name = make_milestone_branch_name(build_id, milestone_id)

    # Find available ports
    try:
        backend_port, frontend_port = find_available_ports(build_id, milestone_id)
    except RuntimeError as e:
        return None, str(e)

    # Create worktree
    worktree_path, error = create_worktree(build_id, milestone_id, branch_name, logger)
    if error:
        return None, error

    # Set up environment
    setup_worktree_environment(worktree_path, backend_port, frontend_port, logger)

    # Update milestone state
    state.update_milestone(
        milestone_id,
        status="in_progress",
        worktree_path=worktree_path,
        backend_port=backend_port,
        frontend_port=frontend_port,
        branch_name=branch_name,
    )
    state.set_current_milestone(milestone_id)
    state.save(workflow_step=f"setup_milestone:{milestone_id}")

    logger.info(
        f"Set up milestone {milestone_id}: worktree={worktree_path}, "
        f"ports={backend_port}/{frontend_port}, branch={branch_name}"
    )

    return worktree_path, None


def complete_milestone(
    state: BuildState, milestone_id: str, logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Complete a milestone: merge worktree to main, clean up, update state.

    Args:
        state: Current build state
        milestone_id: The milestone to complete
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    build_id = state.build_id
    milestone = state.get_milestone(milestone_id)

    if not milestone:
        return False, f"Milestone {milestone_id} not found"

    branch_name = milestone.get("branch_name")
    worktree_path = milestone.get("worktree_path")

    if not branch_name:
        return False, f"No branch name for milestone {milestone_id}"

    # Commit any remaining changes in the worktree
    if worktree_path and os.path.exists(worktree_path):
        success, error = commit_changes(
            f"build-os: complete milestone {milestone_id}", cwd=worktree_path
        )
        if not success and error:
            logger.warning(f"Commit warning: {error}")

    # Merge to main
    from .utils import get_project_root

    project_root = get_project_root()
    success, error = merge_branch_to_main(branch_name, cwd=project_root, logger=logger)
    if not success:
        return False, f"Failed to merge milestone {milestone_id}: {error}"

    # Remove worktree
    remove_worktree(build_id, milestone_id, logger)

    # Update state
    state.update_milestone(
        milestone_id,
        status="complete",
        worktree_path=None,
    )

    # Clear current milestone
    next_milestone = state.get_next_pending_milestone()
    state.set_current_milestone(next_milestone["id"] if next_milestone else None)
    state.save(workflow_step=f"complete_milestone:{milestone_id}")

    logger.info(f"Completed milestone {milestone_id}")
    return True, None


def advance_milestone_status(
    state: BuildState, milestone_id: str, new_status: MilestoneStatus, logger: logging.Logger
) -> None:
    """Advance a milestone to the next status and save.

    Args:
        state: Current build state
        milestone_id: The milestone to advance
        new_status: The new status to set
        logger: Logger instance
    """
    state.update_milestone(milestone_id, status=new_status)
    state.save(workflow_step=f"advance:{milestone_id}:{new_status}")
    logger.info(f"Milestone {milestone_id} → {new_status}")


def get_milestone_summary(state: BuildState) -> str:
    """Generate a human-readable milestone progress summary."""
    milestones = state.get_milestones()
    if not milestones:
        return "No milestones found."

    status_icons = {
        "pending": "[ ]",
        "in_progress": "[~]",
        "frontend_done": "[F]",
        "backend_done": "[B]",
        "wired": "[W]",
        "tested": "[T]",
        "complete": "[x]",
    }

    lines = [f"Build: {state.build_id} | Product: {state.get('product_name', 'Unknown')}"]
    lines.append("-" * 60)

    total = len(milestones)
    complete = sum(1 for m in milestones if m["status"] == "complete")

    for m in milestones:
        icon = status_icons.get(m["status"], "[?]")
        section = f" ({m.get('section_id', 'shell')})" if m.get("section_id") else ""
        port_info = ""
        if m.get("backend_port"):
            port_info = f" | ports: {m['backend_port']}/{m['frontend_port']}"
        lines.append(f"  {icon} {m['id']}: {m['name']}{section} — {m['status']}{port_info}")

    lines.append("-" * 60)
    lines.append(f"Progress: {complete}/{total} milestones complete")

    cost = state.get("total_cost", 0.0)
    if cost > 0:
        lines.append(f"Total cost: ${cost:.4f}")

    return "\n".join(lines)
