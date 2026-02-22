"""Build OS: Single milestone orchestrator.

Chains steps for one milestone: build-section → build-api → wire-data → validate.

Usage:
    uv run python adws/adw_workflows/build_milestone.py --build-id <id> --milestone-id <milestone>
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


async def run_milestone(build_id: str, milestone_id: str) -> bool:
    """Run a single milestone through the full pipeline.

    Args:
        build_id: The build ID
        milestone_id: The milestone ID to build

    Returns:
        True if milestone completed successfully
    """
    logger = setup_logger(build_id, f"milestone_{milestone_id}")
    check_env_vars(logger)

    state = BuildState.load(build_id, logger)
    if not state:
        logger.error(f"No build state found for build_id: {build_id}")
        return False

    milestone = state.get_milestone(milestone_id)
    if not milestone:
        logger.error(f"Milestone {milestone_id} not found")
        return False

    if milestone["status"] == "complete":
        logger.info(f"Milestone {milestone_id} is already complete")
        return True

    section_id = milestone.get("section_id")
    logger.info(f"Building milestone: {milestone_id} ({milestone['name']})")

    # Set up worktree
    worktree_path, error = setup_milestone(state, milestone_id, logger)
    if error:
        logger.error(f"Failed to set up milestone: {error}")
        return False

    working_dir = worktree_path or state.get("output_path")

    if section_id is None:
        # Shell milestone
        response = execute_template(
            AgentTemplateRequest(
                agent_name="shell_builder",
                slash_command="/build-os/build-shell",
                build_id=build_id,
                working_dir=working_dir,
            )
        )
        if not response.success:
            logger.error(f"Shell build failed: {response.output[:200]}")
            return False
    else:
        # Section milestone — run all 4 steps
        steps = [
            ("/build-os/build-section", "section_builder", "frontend_done"),
            ("/build-os/build-api", "api_builder", "backend_done"),
            ("/build-os/wire-data", "wire_builder", "wired"),
            ("/build-os/validate", "validator", "tested"),
        ]

        for slash_cmd, agent_name, next_status in steps:
            # Skip steps already completed
            current_status = state.get_milestone(milestone_id)["status"]
            status_order = [
                "pending", "in_progress", "frontend_done",
                "backend_done", "wired", "tested", "complete",
            ]
            if status_order.index(current_status) >= status_order.index(next_status):
                logger.info(f"Skipping {slash_cmd} — already at {current_status}")
                continue

            logger.info(f"Running {slash_cmd} {section_id}...")
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
                logger.error(f"{slash_cmd} failed: {response.output[:200]}")
                return False

            advance_milestone_status(state, milestone_id, next_status, logger)

    # Complete milestone
    success, error = complete_milestone(state, milestone_id, logger)
    if not success:
        logger.error(f"Failed to complete milestone: {error}")
        return False

    logger.info(f"Milestone {milestone_id} complete!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build OS: Single milestone orchestrator")
    parser.add_argument("--build-id", required=True, help="Build ID")
    parser.add_argument("--milestone-id", required=True, help="Milestone ID to build")
    args = parser.parse_args()

    success = asyncio.run(run_milestone(args.build_id, args.milestone_id))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
