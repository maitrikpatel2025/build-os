"""Worktree and port management for Build OS isolated milestones.

Provides utilities for creating/managing git worktrees under trees/{build_id}-{milestone_id}/
and allocating unique ports for each isolated instance.

Port ranges: Backend 9300-9314, Frontend 9400-9414 (avoids Agent HQ 9100-9214).
"""

import logging
import os
import shutil
import socket
import subprocess
from typing import Optional, Tuple

from .utils import get_project_root


def create_worktree(
    build_id: str, milestone_id: str, branch_name: str, logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git worktree for an isolated milestone build.

    Args:
        build_id: The build ID
        milestone_id: The milestone ID (e.g., "01-shell", "02-dashboard")
        branch_name: The branch name to create
        logger: Logger instance

    Returns:
        Tuple of (worktree_path, error_message)
    """
    project_root = get_project_root()
    trees_dir = os.path.join(project_root, "trees")
    os.makedirs(trees_dir, exist_ok=True)

    worktree_id = f"{build_id}-{milestone_id}"
    worktree_path = os.path.join(trees_dir, worktree_id)

    if os.path.exists(worktree_path):
        logger.warning(f"Worktree already exists at {worktree_path}")
        return worktree_path, None

    # Fetch latest from origin
    logger.info("Fetching latest changes from origin")
    fetch_result = subprocess.run(
        ["git", "fetch", "origin"], capture_output=True, text=True, cwd=project_root
    )
    if fetch_result.returncode != 0:
        logger.warning(f"Failed to fetch from origin: {fetch_result.stderr}")

    # Create worktree branching from origin/main
    cmd = ["git", "worktree", "add", "-b", branch_name, worktree_path, "origin/main"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    if result.returncode != 0:
        if "already exists" in result.stderr:
            cmd = ["git", "worktree", "add", worktree_path, branch_name]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=project_root
            )

        if result.returncode != 0:
            error_msg = f"Failed to create worktree: {result.stderr}"
            logger.error(error_msg)
            return None, error_msg

    logger.info(f"Created worktree at {worktree_path} for branch {branch_name}")
    return worktree_path, None


def validate_worktree(build_id: str, milestone_id: str) -> Tuple[bool, Optional[str]]:
    """Validate a worktree exists in filesystem and git.

    Returns:
        Tuple of (is_valid, error_message)
    """
    worktree_path = get_worktree_path(build_id, milestone_id)

    if not os.path.exists(worktree_path):
        return False, f"Worktree directory not found: {worktree_path}"

    project_root = get_project_root()
    result = subprocess.run(
        ["git", "worktree", "list"],
        capture_output=True,
        text=True,
        cwd=project_root,
    )
    if worktree_path not in result.stdout:
        return False, "Worktree not registered with git"

    return True, None


def get_worktree_path(build_id: str, milestone_id: str) -> str:
    """Get absolute path to a milestone's worktree."""
    project_root = get_project_root()
    worktree_id = f"{build_id}-{milestone_id}"
    return os.path.join(project_root, "trees", worktree_id)


def remove_worktree(
    build_id: str, milestone_id: str, logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Remove a worktree and clean up."""
    worktree_path = get_worktree_path(build_id, milestone_id)
    project_root = get_project_root()

    cmd = ["git", "worktree", "remove", worktree_path, "--force"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    if result.returncode != 0:
        if os.path.exists(worktree_path):
            try:
                shutil.rmtree(worktree_path)
                logger.warning(f"Manually removed worktree directory: {worktree_path}")
            except Exception as e:
                return False, f"Failed to remove worktree: {result.stderr}, manual cleanup failed: {e}"

    logger.info(f"Removed worktree at {worktree_path}")
    return True, None


def setup_worktree_environment(
    worktree_path: str, backend_port: int, frontend_port: int, logger: logging.Logger
) -> None:
    """Set up worktree environment by creating .ports.env file."""
    ports_env_path = os.path.join(worktree_path, ".ports.env")

    with open(ports_env_path, "w") as f:
        f.write(f"BACKEND_PORT={backend_port}\n")
        f.write(f"FRONTEND_PORT={frontend_port}\n")
        f.write(f"VITE_BACKEND_URL=http://localhost:{backend_port}\n")

    logger.info(f"Created .ports.env with Backend: {backend_port}, Frontend: {frontend_port}")


def list_active_worktrees() -> list:
    """List all active Build OS worktrees."""
    project_root = get_project_root()
    trees_dir = os.path.join(project_root, "trees")

    if not os.path.exists(trees_dir):
        return []

    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    worktrees = []
    if result.returncode == 0:
        for line in result.stdout.split("\n"):
            if line.startswith("worktree ") and "/trees/" in line:
                path = line.replace("worktree ", "")
                name = os.path.basename(path)
                worktrees.append({"path": path, "name": name})

    return worktrees


# Port management functions

# Build OS port ranges (avoid Agent HQ 9100-9214)
BACKEND_PORT_BASE = 9300
FRONTEND_PORT_BASE = 9400
MAX_CONCURRENT_SLOTS = 15


def get_ports_for_milestone(build_id: str, milestone_id: str) -> Tuple[int, int]:
    """Deterministically assign ports based on build ID and milestone ID."""
    combined = f"{build_id}-{milestone_id}"
    try:
        id_chars = "".join(c for c in combined[:12] if c.isalnum())
        index = int(id_chars, 36) % MAX_CONCURRENT_SLOTS
    except ValueError:
        index = hash(combined) % MAX_CONCURRENT_SLOTS

    backend_port = BACKEND_PORT_BASE + index
    frontend_port = FRONTEND_PORT_BASE + index

    return backend_port, frontend_port


def is_port_available(port: int) -> bool:
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(("localhost", port))
            return True
    except (socket.error, OSError):
        return False


def find_available_ports(
    build_id: str, milestone_id: str, max_attempts: int = 15
) -> Tuple[int, int]:
    """Find available ports starting from deterministic assignment.

    Raises:
        RuntimeError: If no available ports found
    """
    base_backend, base_frontend = get_ports_for_milestone(build_id, milestone_id)
    base_index = base_backend - BACKEND_PORT_BASE

    for offset in range(max_attempts):
        index = (base_index + offset) % MAX_CONCURRENT_SLOTS
        backend_port = BACKEND_PORT_BASE + index
        frontend_port = FRONTEND_PORT_BASE + index

        if is_port_available(backend_port) and is_port_available(frontend_port):
            return backend_port, frontend_port

    raise RuntimeError(
        f"No available ports in range {BACKEND_PORT_BASE}-{BACKEND_PORT_BASE + MAX_CONCURRENT_SLOTS - 1}"
    )
