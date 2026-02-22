"""Build OS: Full pipeline orchestrator.

Chains all build steps automatically:
init → scaffold → shell → (section → api → wire → validate) × N → finalize

Usage:
    uv run python adws/adw_workflows/build_all.py --build-id <id>
"""

import argparse
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.build_state import BuildState
from adw_modules.agent import execute_template
from adw_modules.agent_sdk import (
    create_log_hooks,
    create_message_handlers,
)
from adw_modules.milestone_ops import (
    setup_milestone,
    complete_milestone,
    advance_milestone_status,
    get_milestone_summary,
)
from adw_modules.worktree_ops import create_worktree, find_available_ports
from adw_modules.git_ops import make_milestone_branch_name
from adw_modules.data_types import AgentTemplateRequest
from adw_modules.utils import setup_logger, check_env_vars


async def run_pipeline(build_id: str) -> bool:
    """Run the full Build OS pipeline for a given build.

    Args:
        build_id: The build ID to process

    Returns:
        True if pipeline completed successfully
    """
    logger = setup_logger(build_id, "build_all")
    check_env_vars(logger)

    # Load build state
    state = BuildState.load(build_id, logger)
    if not state:
        logger.error(f"No build state found for build_id: {build_id}")
        return False

    logger.info(f"Starting full pipeline for: {state.get('product_name')}")
    logger.info(get_milestone_summary(state))

    # Process each milestone
    milestones = state.get_milestones()
    for milestone in milestones:
        if milestone["status"] == "complete":
            logger.info(f"Skipping completed milestone: {milestone['id']}")
            continue

        milestone_id = milestone["id"]
        section_id = milestone.get("section_id")

        logger.info(f"\n{'='*60}")
        logger.info(f"Building milestone: {milestone_id} ({milestone['name']})")
        logger.info(f"{'='*60}")

        # Set up worktree for this milestone
        worktree_path, error = setup_milestone(state, milestone_id, logger)
        if error:
            logger.error(f"Failed to set up milestone {milestone_id}: {error}")
            return False

        working_dir = worktree_path or state.get("output_path")

        if section_id is None:
            # Shell milestone — single step
            success = await _build_shell(state, milestone_id, working_dir, logger)
        else:
            # Section milestone — multi-step pipeline
            success = await _build_section_pipeline(
                state, milestone_id, section_id, working_dir, logger
            )

        if not success:
            logger.error(f"Milestone {milestone_id} failed")
            return False

        # Complete the milestone (merge + cleanup)
        success, error = complete_milestone(state, milestone_id, logger)
        if not success:
            logger.error(f"Failed to complete milestone {milestone_id}: {error}")
            return False

        logger.info(f"Milestone {milestone_id} complete!")

    # Finalize
    logger.info("\n" + "=" * 60)
    logger.info("All milestones complete — finalizing build")
    logger.info("=" * 60)

    response = execute_template(
        AgentTemplateRequest(
            agent_name="finalizer",
            slash_command="/build-os/finalize",
            build_id=build_id,
        )
    )

    if not response.success:
        logger.warning(f"Finalization had issues: {response.output[:200]}")

    # Final summary
    state = BuildState.load(build_id, logger)
    logger.info("\n" + get_milestone_summary(state))
    logger.info("Pipeline complete!")

    return True


async def _build_shell(
    state: BuildState, milestone_id: str, working_dir: str, logger: logging.Logger
) -> bool:
    """Build the application shell."""
    logger.info("Building shell...")

    response = execute_template(
        AgentTemplateRequest(
            agent_name="shell_builder",
            slash_command="/build-os/build-shell",
            build_id=state.build_id,
            working_dir=working_dir,
        )
    )

    if not response.success:
        logger.error(f"Shell build failed: {response.output[:200]}")
        return False

    advance_milestone_status(state, milestone_id, "complete", logger)
    return True


async def _build_section_pipeline(
    state: BuildState,
    milestone_id: str,
    section_id: str,
    working_dir: str,
    logger: logging.Logger,
) -> bool:
    """Build a section through the full pipeline: frontend → API → wire → validate."""

    # Step 1: Build frontend
    logger.info(f"Building frontend for {section_id}...")
    response = execute_template(
        AgentTemplateRequest(
            agent_name="section_builder",
            slash_command="/build-os/build-section",
            args=[section_id],
            build_id=state.build_id,
            working_dir=working_dir,
        )
    )

    if not response.success:
        logger.error(f"Frontend build failed for {section_id}: {response.output[:200]}")
        return False

    advance_milestone_status(state, milestone_id, "frontend_done", logger)

    # Step 2: Build API
    logger.info(f"Building API for {section_id}...")
    response = execute_template(
        AgentTemplateRequest(
            agent_name="api_builder",
            slash_command="/build-os/build-api",
            args=[section_id],
            build_id=state.build_id,
            working_dir=working_dir,
        )
    )

    if not response.success:
        logger.error(f"API build failed for {section_id}: {response.output[:200]}")
        return False

    advance_milestone_status(state, milestone_id, "backend_done", logger)

    # Step 3: Wire data
    logger.info(f"Wiring data for {section_id}...")
    response = execute_template(
        AgentTemplateRequest(
            agent_name="wire_builder",
            slash_command="/build-os/wire-data",
            args=[section_id],
            build_id=state.build_id,
            working_dir=working_dir,
        )
    )

    if not response.success:
        logger.error(f"Wire data failed for {section_id}: {response.output[:200]}")
        return False

    advance_milestone_status(state, milestone_id, "wired", logger)

    # Step 4: Validate
    logger.info(f"Validating {section_id}...")
    response = execute_template(
        AgentTemplateRequest(
            agent_name="validator",
            slash_command="/build-os/validate",
            args=[section_id],
            build_id=state.build_id,
            working_dir=working_dir,
        )
    )

    if not response.success:
        logger.error(f"Validation failed for {section_id}: {response.output[:200]}")
        return False

    advance_milestone_status(state, milestone_id, "tested", logger)
    return True


def main():
    parser = argparse.ArgumentParser(description="Build OS: Full pipeline orchestrator")
    parser.add_argument("--build-id", required=True, help="Build ID to process")
    args = parser.parse_args()

    success = asyncio.run(run_pipeline(args.build_id))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import logging

    main()
