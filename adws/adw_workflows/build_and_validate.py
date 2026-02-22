"""Build OS: Build and validate one milestone.

Full pipeline for a single section: build-section → build-api → wire-data → validate.

Usage:
    uv run python adws/adw_workflows/build_and_validate.py --build-id <id> --section-id <section>
"""

import argparse
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.build_state import BuildState
from adw_modules.agent import execute_template
from adw_modules.milestone_ops import (
    setup_milestone,
    complete_milestone,
    advance_milestone_status,
)
from adw_modules.data_types import AgentTemplateRequest
from adw_modules.utils import setup_logger, check_env_vars


async def run_build_and_validate(build_id: str, section_id: str) -> bool:
    """Build and validate one section end-to-end.

    Args:
        build_id: The build ID
        section_id: The section to build and validate

    Returns:
        True if section built and validated successfully
    """
    logger = setup_logger(build_id, f"build_validate_{section_id}")
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

    if milestone["status"] == "complete":
        logger.info(f"Section {section_id} is already complete")
        return True

    logger.info(f"Building and validating section: {section_id}")

    # Set up worktree
    worktree_path, error = setup_milestone(state, milestone_id, logger)
    if error:
        logger.error(f"Failed to set up milestone: {error}")
        return False

    working_dir = worktree_path or state.get("output_path")

    # Pipeline steps with status tracking
    steps = [
        ("/build-os/build-section", "section_builder", "frontend_done", "Building frontend"),
        ("/build-os/build-api", "api_builder", "backend_done", "Building API"),
        ("/build-os/wire-data", "wire_builder", "wired", "Wiring data"),
        ("/build-os/validate", "validator", "tested", "Validating"),
    ]

    status_order = [
        "pending", "in_progress", "frontend_done",
        "backend_done", "wired", "tested", "complete",
    ]

    for slash_cmd, agent_name, next_status, description in steps:
        current_status = state.get_milestone(milestone_id)["status"]

        # Skip steps already completed
        if status_order.index(current_status) >= status_order.index(next_status):
            logger.info(f"Skipping {description} — already at {current_status}")
            continue

        logger.info(f"{description} for {section_id}...")

        response = execute_template(
            AgentTemplateRequest(
                agent_name=agent_name,
                slash_command=slash_cmd,
                args=[section_id],
                build_id=build_id,
                working_dir=working_dir,
            )
        )

        if not response.success:
            logger.error(f"{description} failed: {response.output[:200]}")
            return False

        advance_milestone_status(state, milestone_id, next_status, logger)
        logger.info(f"{description} complete!")

    # Complete milestone
    success, error = complete_milestone(state, milestone_id, logger)
    if not success:
        logger.error(f"Failed to complete milestone: {error}")
        return False

    logger.info(f"Section {section_id} built and validated!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build OS: Build and validate one section")
    parser.add_argument("--build-id", required=True, help="Build ID")
    parser.add_argument("--section-id", required=True, help="Section ID to build and validate")
    args = parser.parse_args()

    success = asyncio.run(run_build_and_validate(args.build_id, args.section_id))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
