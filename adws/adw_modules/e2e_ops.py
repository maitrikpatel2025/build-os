"""E2E test orchestrator for Build OS.

Provides programmatic e2e test execution via /build-os/test-e2e-section
and auto-resolution via /resolve_failed_e2e_test, with retry logic.
"""

import json
import logging
from typing import Optional

from .agent import execute_template
from .build_state import BuildState
from .data_types import AgentTemplateRequest, E2ETestResult


def parse_e2e_test_results(output: str) -> Optional[E2ETestResult]:
    """Parse E2E test results JSON from agent output.

    The agent output may contain markdown, prose, or other text around
    a JSON block. We extract the first valid JSON object that matches
    the E2ETestResult schema.

    Args:
        output: Raw string output from the agent.

    Returns:
        E2ETestResult if valid JSON found, None otherwise.
    """
    if not output or not output.strip():
        return None

    # Try direct parse first
    try:
        data = json.loads(output.strip())
        if isinstance(data, dict) and "test_name" in data and "status" in data:
            return E2ETestResult(**data)
    except (json.JSONDecodeError, Exception):
        pass

    # Try extracting from markdown code block
    for fence in ["```json", "```"]:
        if fence in output:
            start = output.index(fence) + len(fence)
            end = output.find("```", start)
            if end != -1:
                candidate = output[start:end].strip()
                try:
                    data = json.loads(candidate)
                    if isinstance(data, dict) and "test_name" in data and "status" in data:
                        return E2ETestResult(**data)
                except (json.JSONDecodeError, Exception):
                    pass

    # Try finding JSON object by braces
    brace_start = output.find("{")
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(output)):
            if output[i] == "{":
                depth += 1
            elif output[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = output[brace_start : i + 1]
                    try:
                        data = json.loads(candidate)
                        if isinstance(data, dict) and "test_name" in data and "status" in data:
                            return E2ETestResult(**data)
                    except (json.JSONDecodeError, Exception):
                        pass
                    break

    return None


def run_e2e_for_section(
    state: BuildState,
    milestone_id: str,
    section_id: str,
    working_dir: str,
    logger: logging.Logger,
) -> Optional[E2ETestResult]:
    """Execute /build-os/test-e2e-section for a section.

    Args:
        state: Current build state.
        milestone_id: The milestone being tested.
        section_id: The section to run e2e tests for.
        working_dir: Worktree or output path to run from.
        logger: Logger instance.

    Returns:
        E2ETestResult if tests completed, None if execution failed.
    """
    build_id = state.build_id
    logger.info(f"Running e2e tests for section: {section_id}")

    response = execute_template(
        AgentTemplateRequest(
            agent_name="e2e_test_runner",
            slash_command="/build-os/test-e2e-section",
            args=[build_id, section_id],
            build_id=build_id,
            working_dir=working_dir,
        )
    )

    if not response.success:
        logger.error(f"E2E test execution failed: {response.output[:200]}")
        return None

    result = parse_e2e_test_results(response.output)
    if not result:
        logger.error("Failed to parse e2e test results from agent output")
        return None

    # Update milestone with results
    e2e_status = "complete" if result.status == "passed" else "failed"
    state.update_milestone(
        milestone_id,
        e2e_test_status=e2e_status,
        e2e_test_results=result.model_dump(),
    )
    state.save(workflow_step=f"e2e_test:{section_id}")

    logger.info(f"E2E test result for {section_id}: {result.status}")
    return result


def resolve_e2e_failure(
    state: BuildState,
    section_id: str,
    failure_json: str,
    working_dir: str,
    logger: logging.Logger,
) -> bool:
    """Execute /resolve_failed_e2e_test to fix a failing e2e test.

    Args:
        state: Current build state.
        section_id: The section with the failure.
        failure_json: JSON string of the E2ETestResult failure.
        working_dir: Worktree or output path to fix code in.
        logger: Logger instance.

    Returns:
        True if resolution agent completed successfully.
    """
    build_id = state.build_id
    logger.info(f"Attempting to resolve e2e failure for section: {section_id}")

    # /resolve_failed_e2e_test is a top-level command, not under /build-os/
    # We invoke it via prompt_claude_code_with_retry directly
    import os

    from .agent import prompt_claude_code_with_retry
    from .data_types import AgentPromptRequest
    from .utils import get_project_root

    project_root = get_project_root()
    output_dir = os.path.join(project_root, "agents", build_id, "e2e_resolver")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "raw_output.jsonl")

    prompt = f"/resolve_failed_e2e_test {failure_json}"

    request = AgentPromptRequest(
        prompt=prompt,
        build_id=build_id,
        agent_name="e2e_resolver",
        model="sonnet",
        dangerously_skip_permissions=True,
        output_file=output_file,
        working_dir=working_dir,
    )

    response = prompt_claude_code_with_retry(request, max_retries=1)

    if response.success:
        logger.info(f"E2E resolution completed for {section_id}")
        return True

    logger.error(f"E2E resolution failed for {section_id}: {response.output[:200]}")
    return False


def run_e2e_with_resolution(
    state: BuildState,
    milestone_id: str,
    section_id: str,
    working_dir: str,
    logger: logging.Logger,
    max_retries: int = 2,
) -> Optional[E2ETestResult]:
    """Run e2e tests with auto-resolution retry loop.

    Executes /build-os/test-e2e-section. If tests fail, runs
    /resolve_failed_e2e_test and re-runs e2e (up to max_retries).

    Args:
        state: Current build state.
        milestone_id: The milestone being tested.
        section_id: The section to test.
        working_dir: Worktree or output path.
        logger: Logger instance.
        max_retries: Max resolution attempts (default 2).

    Returns:
        Final E2ETestResult, or None if execution failed entirely.
    """
    result = run_e2e_for_section(state, milestone_id, section_id, working_dir, logger)

    if result is None:
        return None

    if result.status == "passed":
        return result

    # Retry loop: resolve failure then re-run
    for attempt in range(1, max_retries + 1):
        logger.info(f"E2E resolution attempt {attempt}/{max_retries} for {section_id}")

        failure_json = result.model_dump_json()
        resolved = resolve_e2e_failure(state, section_id, failure_json, working_dir, logger)

        if not resolved:
            logger.warning(f"Resolution attempt {attempt} failed for {section_id}")
            continue

        result = run_e2e_for_section(state, milestone_id, section_id, working_dir, logger)

        if result is None:
            return None

        if result.status == "passed":
            logger.info(f"E2E passed after resolution attempt {attempt} for {section_id}")
            return result

    logger.error(f"E2E still failing after {max_retries} resolution attempts for {section_id}")
    return result
