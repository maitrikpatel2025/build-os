"""Git operations for Build OS pipeline.

Provides branch management, commit, merge, and PR operations
adapted for milestone-based workflow.
"""

import json
import logging
import subprocess
from typing import Optional, Tuple


def get_current_branch(cwd: Optional[str] = None) -> str:
    """Get current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout.strip()


def create_branch(
    branch_name: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Create and checkout a new branch."""
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        if "already exists" in result.stderr:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode != 0:
                return False, result.stderr
            return True, None
        return False, result.stderr
    return True, None


def make_milestone_branch_name(build_id: str, milestone_id: str) -> str:
    """Generate branch name for a milestone.

    Format: build-{build_id}-{milestone_id}
    Example: build-a1b2c3d4-02-dashboard
    """
    return f"build-{build_id}-{milestone_id}"


def commit_changes(
    message: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Stage all changes and commit."""
    # Check if there are changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if not result.stdout.strip():
        return True, None  # No changes to commit

    # Stage all changes
    result = subprocess.run(
        ["git", "add", "-A"], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        return False, result.stderr

    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", message], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, None


def push_branch(
    branch_name: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Push branch to remote."""
    result = subprocess.run(
        ["git", "push", "-u", "origin", branch_name],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, None


def merge_branch_to_main(
    branch_name: str, cwd: Optional[str] = None, logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[str]]:
    """Merge a branch into main.

    Args:
        branch_name: Branch to merge
        cwd: Working directory
        logger: Optional logger

    Returns:
        Tuple of (success, error_message)
    """
    # Checkout main
    result = subprocess.run(
        ["git", "checkout", "main"], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        return False, f"Failed to checkout main: {result.stderr}"

    # Merge the branch
    result = subprocess.run(
        ["git", "merge", branch_name, "--no-ff", "-m", f"Merge {branch_name} into main"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return False, f"Failed to merge {branch_name}: {result.stderr}"

    if logger:
        logger.info(f"Merged {branch_name} into main")

    return True, None


def init_git_repo(path: str, logger: Optional[logging.Logger] = None) -> Tuple[bool, Optional[str]]:
    """Initialize a git repo and make initial commit."""
    result = subprocess.run(
        ["git", "init"], capture_output=True, text=True, cwd=path
    )
    if result.returncode != 0:
        return False, f"Failed to init git: {result.stderr}"

    # Create main branch
    result = subprocess.run(
        ["git", "checkout", "-b", "main"], capture_output=True, text=True, cwd=path
    )

    # Stage and commit
    subprocess.run(["git", "add", "-A"], capture_output=True, text=True, cwd=path)
    result = subprocess.run(
        ["git", "commit", "-m", "Initial scaffold from Build OS"],
        capture_output=True,
        text=True,
        cwd=path,
    )
    if result.returncode != 0:
        return False, f"Failed to commit: {result.stderr}"

    if logger:
        logger.info(f"Initialized git repo at {path}")

    return True, None


def check_pr_exists(branch_name: str, repo_path: Optional[str] = None) -> Optional[str]:
    """Check if PR exists for branch. Returns PR URL if exists."""
    cmd = ["gh", "pr", "list", "--head", branch_name, "--json", "url"]
    if repo_path:
        cmd.extend(["--repo", repo_path])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        prs = json.loads(result.stdout)
        if prs:
            return prs[0]["url"]
    return None
