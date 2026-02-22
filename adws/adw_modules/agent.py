"""Claude Code agent module for executing prompts programmatically.

Adapted from Agent HQ agent.py for Build OS pipeline execution.
"""

import json
import os
import re
import subprocess
import time
from typing import Any, Dict, Final, List, Optional, Tuple

from dotenv import load_dotenv

from .data_types import (
    AgentPromptRequest,
    AgentPromptResponse,
    AgentTemplateRequest,
    BuildSlashCommand,
    ModelSet,
    RetryCode,
)

load_dotenv()

CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")

# Model selection mapping for Build OS slash commands
SLASH_COMMAND_MODEL_MAP: Final[Dict[BuildSlashCommand, Dict[ModelSet, str]]] = {
    "/build-os/init": {"base": "sonnet", "heavy": "sonnet"},
    "/build-os/scaffold": {"base": "sonnet", "heavy": "opus"},
    "/build-os/build-shell": {"base": "sonnet", "heavy": "opus"},
    "/build-os/build-section": {"base": "sonnet", "heavy": "opus"},
    "/build-os/build-api": {"base": "sonnet", "heavy": "opus"},
    "/build-os/wire-data": {"base": "sonnet", "heavy": "opus"},
    "/build-os/validate": {"base": "sonnet", "heavy": "sonnet"},
    "/build-os/build-all": {"base": "sonnet", "heavy": "opus"},
    "/build-os/finalize": {"base": "sonnet", "heavy": "sonnet"},
    "/build-os/status": {"base": "sonnet", "heavy": "sonnet"},
    "/build-os/resume": {"base": "sonnet", "heavy": "opus"},
    "/build-os/test-e2e-section": {"base": "sonnet", "heavy": "opus"},
}


def get_model_for_slash_command(
    request: AgentTemplateRequest, default: str = "sonnet"
) -> str:
    """Get the appropriate model for a template request based on build state."""
    from .build_state import BuildState

    model_set: ModelSet = "base"
    state = BuildState.load(request.build_id)
    if state:
        model_set = state.get("model_set", "base")

    command_config = SLASH_COMMAND_MODEL_MAP.get(request.slash_command)
    if command_config:
        return command_config.get(model_set, command_config.get("base", default))

    return default


def truncate_output(
    output: str, max_length: int = 500, suffix: str = "... (truncated)"
) -> str:
    """Truncate output to a reasonable length for display."""
    if output.startswith('{"type":') and '\n{"type":' in output:
        lines = output.strip().split("\n")
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if data.get("type") == "result":
                    result = data.get("result", "")
                    if result:
                        return truncate_output(result, max_length, suffix)
                elif data.get("type") == "assistant" and data.get("message"):
                    content = data["message"].get("content", [])
                    if isinstance(content, list) and content:
                        text = content[0].get("text", "")
                        if text:
                            return truncate_output(text, max_length, suffix)
            except Exception:
                pass
        return f"[JSONL output with {len(lines)} messages]{suffix}"

    if len(output) <= max_length:
        return output

    truncate_at = max_length - len(suffix)
    newline_pos = output.rfind("\n", truncate_at - 50, truncate_at)
    if newline_pos > 0:
        return output[:newline_pos] + suffix

    space_pos = output.rfind(" ", truncate_at - 20, truncate_at)
    if space_pos > 0:
        return output[:space_pos] + suffix

    return output[:truncate_at] + suffix


def check_claude_installed() -> Optional[str]:
    """Check if Claude Code CLI is installed. Return error message if not."""
    try:
        result = subprocess.run(
            [CLAUDE_PATH, "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
    except FileNotFoundError:
        return f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
    return None


def parse_jsonl_output(
    output_file: str,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse JSONL output file and return all messages and the result message."""
    try:
        with open(output_file, "r") as f:
            messages = [json.loads(line) for line in f if line.strip()]

        result_message = None
        for message in reversed(messages):
            if message.get("type") == "result":
                result_message = message
                break

        return messages, result_message
    except Exception:
        return [], None


def convert_jsonl_to_json(jsonl_file: str) -> str:
    """Convert JSONL file to JSON array file."""
    json_file = jsonl_file.replace(".jsonl", ".json")
    messages, _ = parse_jsonl_output(jsonl_file)

    with open(json_file, "w") as f:
        json.dump(messages, f, indent=2)

    return json_file


def get_claude_env() -> Dict[str, str]:
    """Get environment variables for Claude Code execution."""
    from .utils import get_safe_subprocess_env

    return get_safe_subprocess_env()


def save_prompt(prompt: str, build_id: str, agent_name: str = "ops") -> None:
    """Save a prompt to the logging directory."""
    match = re.match(r"^(/[\w/-]+)", prompt)
    if not match:
        return

    slash_command = match.group(1)
    command_name = slash_command.replace("/", "_").lstrip("_")

    from .utils import get_project_root

    project_root = get_project_root()
    prompt_dir = os.path.join(project_root, "agents", build_id, agent_name, "prompts")
    os.makedirs(prompt_dir, exist_ok=True)

    prompt_file = os.path.join(prompt_dir, f"{command_name}.txt")
    with open(prompt_file, "w") as f:
        f.write(prompt)


def prompt_claude_code_with_retry(
    request: AgentPromptRequest,
    max_retries: int = 3,
    retry_delays: List[int] = None,
) -> AgentPromptResponse:
    """Execute Claude Code with retry logic for certain error types."""
    if retry_delays is None:
        retry_delays = [1, 3, 5]

    while len(retry_delays) < max_retries:
        retry_delays.append(retry_delays[-1] + 2)

    last_response = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            delay = retry_delays[attempt - 1]
            time.sleep(delay)

        response = prompt_claude_code(request)
        last_response = response

        if response.success or response.retry_code == RetryCode.NONE:
            return response

        if response.retry_code in [
            RetryCode.CLAUDE_CODE_ERROR,
            RetryCode.TIMEOUT_ERROR,
            RetryCode.EXECUTION_ERROR,
            RetryCode.ERROR_DURING_EXECUTION,
        ]:
            if attempt < max_retries:
                continue
            else:
                return response

    return last_response


def prompt_claude_code(request: AgentPromptRequest) -> AgentPromptResponse:
    """Execute Claude Code with the given prompt configuration."""
    error_msg = check_claude_installed()
    if error_msg:
        return AgentPromptResponse(
            output=error_msg, success=False, session_id=None, retry_code=RetryCode.NONE
        )

    save_prompt(request.prompt, request.build_id, request.agent_name)

    output_dir = os.path.dirname(request.output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    cmd = [CLAUDE_PATH, "-p", request.prompt]
    cmd.extend(["--model", request.model])
    cmd.extend(["--output-format", "stream-json"])
    cmd.append("--verbose")

    if request.working_dir:
        mcp_config_path = os.path.join(request.working_dir, ".mcp.json")
        if os.path.exists(mcp_config_path):
            cmd.extend(["--mcp-config", mcp_config_path])

    if request.disable_tools:
        cmd.extend(["--tools", ""])

    if request.dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    env = get_claude_env()

    try:
        with open(request.output_file, "w") as output_f:
            result = subprocess.run(
                cmd,
                stdout=output_f,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=request.working_dir,
            )

        if result.returncode == 0:
            messages, result_message = parse_jsonl_output(request.output_file)
            convert_jsonl_to_json(request.output_file)

            if result_message:
                session_id = result_message.get("session_id")
                is_error = result_message.get("is_error", False)
                subtype = result_message.get("subtype", "")

                if subtype == "error_during_execution":
                    return AgentPromptResponse(
                        output="Error during execution: Agent encountered an error",
                        success=False,
                        session_id=session_id,
                        retry_code=RetryCode.ERROR_DURING_EXECUTION,
                    )

                result_text = result_message.get("result", "")

                if is_error and len(result_text) > 1000:
                    result_text = truncate_output(result_text, max_length=800)

                return AgentPromptResponse(
                    output=result_text,
                    success=not is_error,
                    session_id=session_id,
                    retry_code=RetryCode.NONE,
                )
            else:
                return AgentPromptResponse(
                    output="No result message found in Claude Code output",
                    success=False,
                    session_id=None,
                    retry_code=RetryCode.NONE,
                )
        else:
            stderr_msg = result.stderr.strip() if result.stderr else ""
            error_from_jsonl = None

            try:
                if os.path.exists(request.output_file):
                    messages, result_message = parse_jsonl_output(request.output_file)
                    if result_message and result_message.get("is_error"):
                        error_from_jsonl = result_message.get("result", "Unknown error")
            except Exception:
                pass

            if error_from_jsonl:
                error_msg = f"Claude Code error: {error_from_jsonl}"
            elif stderr_msg:
                error_msg = f"Claude Code error: {stderr_msg}"
            else:
                error_msg = f"Claude Code error: Command failed with exit code {result.returncode}"

            return AgentPromptResponse(
                output=truncate_output(error_msg, max_length=800),
                success=False,
                session_id=None,
                retry_code=RetryCode.CLAUDE_CODE_ERROR,
            )

    except subprocess.TimeoutExpired:
        return AgentPromptResponse(
            output="Error: Claude Code command timed out",
            success=False,
            session_id=None,
            retry_code=RetryCode.TIMEOUT_ERROR,
        )
    except Exception as e:
        return AgentPromptResponse(
            output=f"Error executing Claude Code: {e}",
            success=False,
            session_id=None,
            retry_code=RetryCode.EXECUTION_ERROR,
        )


def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute a Claude Code template with slash command and arguments."""
    mapped_model = get_model_for_slash_command(request)
    request = request.model_copy(update={"model": mapped_model})

    prompt = f"{request.slash_command} {' '.join(request.args)}"

    from .utils import get_project_root

    project_root = get_project_root()
    output_dir = os.path.join(
        project_root, "agents", request.build_id, request.agent_name
    )
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "raw_output.jsonl")

    prompt_request = AgentPromptRequest(
        prompt=prompt,
        build_id=request.build_id,
        agent_name=request.agent_name,
        model=request.model,
        dangerously_skip_permissions=True,
        output_file=output_file,
        working_dir=request.working_dir,
        disable_tools=request.disable_tools,
    )

    return prompt_claude_code_with_retry(prompt_request)
