"""Build OS: Frontend-only builder for one section.

Builds only the frontend for a single section without API, wiring, or validation.

Usage:
    uv run python adws/adw_workflows/build_section_only.py --build-id <id> --section-id <section>
"""

import argparse
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.build_state import BuildState
from adw_modules.agent import execute_template
from adw_modules.milestone_ops import setup_milestone, advance_milestone_status
from adw_modules.data_types import AgentTemplateRequest
from adw_modules.utils import setup_logger, check_env_vars


async def run_section_frontend(build_id: str, section_id: str) -> bool:
    """Build only the frontend for one section.

    Args:
        build_id: The build ID
        section_id: The section to build

    Returns:
        True if frontend build succeeded
    """
    logger = setup_logger(build_id, f"section_{section_id}")
    check_env_vars(logger)

    state = BuildState.load(build_id, logger)
    if not state:
        logger.error(f"No build state found for build_id: {build_id}")
        return False

    # Find milestone for this section
    milestone = None
    for m in state.get_milestones():
        if m.get("section_id") == section_id:
            milestone = m
            break

    if not milestone:
        logger.error(f"No milestone found for section: {section_id}")
        return False

    milestone_id = milestone["id"]

    if milestone["status"] not in ("pending", "in_progress"):
        logger.info(f"Section {section_id} frontend already built (status: {milestone['status']})")
        return True

    logger.info(f"Building frontend for section: {section_id}")

    # Set up worktree
    worktree_path, error = setup_milestone(state, milestone_id, logger)
    if error:
        logger.error(f"Failed to set up milestone: {error}")
        return False

    working_dir = worktree_path or state.get("output_path")

    # Build frontend
    response = execute_template(
        AgentTemplateRequest(
            agent_name="section_builder",
            slash_command="/build-os/build-section",
            args=[section_id],
            build_id=build_id,
            working_dir=working_dir,
        )
    )

    if not response.success:
        logger.error(f"Frontend build failed: {response.output[:200]}")
        return False

    advance_milestone_status(state, milestone_id, "frontend_done", logger)
    logger.info(f"Frontend for {section_id} complete!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build OS: Frontend-only section builder")
    parser.add_argument("--build-id", required=True, help="Build ID")
    parser.add_argument("--section-id", required=True, help="Section ID to build")
    args = parser.parse_args()

    success = asyncio.run(run_section_frontend(args.build_id, args.section_id))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
