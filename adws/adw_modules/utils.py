"""Utility functions for Build OS system."""

import json
import logging
import os
import re
import sys
import uuid
from typing import Any, TypeVar, Type, Union, Dict, Optional, Tuple, Literal

T = TypeVar("T")

AuthMode = Literal["oauth", "api_key", "none"]


def get_project_root() -> str:
    """Get the Build OS project root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_build_id() -> str:
    """Generate a short 8-character UUID for build tracking."""
    return str(uuid.uuid4())[:8]


def setup_logger(build_id: str, step_name: str = "build") -> logging.Logger:
    """Set up logger that writes to both console and file.

    Args:
        build_id: The build workflow ID
        step_name: Name of the current step (e.g., "init", "scaffold", "build-shell")

    Returns:
        Configured logger instance
    """
    project_root = get_project_root()
    log_dir = os.path.join(project_root, "agents", build_id, step_name)
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "execution.log")

    logger = logging.getLogger(f"build_{build_id}")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_formatter = logging.Formatter("%(message)s")

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Build OS Logger initialized - Build ID: {build_id}")
    logger.debug(f"Log file: {log_file}")

    return logger


def get_logger(build_id: str) -> logging.Logger:
    """Get existing logger by build ID."""
    return logging.getLogger(f"build_{build_id}")


def parse_json(text: str, target_type: Type[T] = None) -> Union[T, Any]:
    """Parse JSON that may be wrapped in markdown code blocks.

    Args:
        text: String containing JSON, possibly wrapped in markdown
        target_type: Optional Pydantic type to validate/parse the result into

    Returns:
        Parsed JSON object, optionally validated as target_type

    Raises:
        ValueError: If JSON cannot be parsed from the text
    """
    # Try to extract JSON from markdown code blocks
    code_block_pattern = r"```(?:json)?\s*\n(.*?)\n```"
    match = re.search(code_block_pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
    else:
        json_str = text.strip()

    # Try to find JSON boundaries if not already clean
    if not (json_str.startswith("[") or json_str.startswith("{")):
        array_start = json_str.find("[")
        array_end = json_str.rfind("]")
        obj_start = json_str.find("{")
        obj_end = json_str.rfind("}")

        if array_start != -1 and (obj_start == -1 or array_start < obj_start):
            if array_end != -1:
                json_str = json_str[array_start : array_end + 1]
        elif obj_start != -1:
            if obj_end != -1:
                json_str = json_str[obj_start : obj_end + 1]

    try:
        result = json.loads(json_str)

        if target_type and hasattr(target_type, "__origin__"):
            if target_type.__origin__ == list:
                item_type = target_type.__args__[0]
                if hasattr(item_type, "model_validate"):
                    result = [item_type.model_validate(item) for item in result]
        elif target_type:
            if hasattr(target_type, "model_validate"):
                result = target_type.model_validate(result)

        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}. Text was: {json_str[:200]}...")


def check_claude_oauth_status() -> Tuple[bool, str]:
    """Check if Claude Code CLI is authenticated via OAuth."""
    claude_config_path = os.path.expanduser("~/.claude.json")

    try:
        if os.path.exists(claude_config_path):
            with open(claude_config_path, "r") as f:
                config = json.load(f)

            if "oauthAccount" in config:
                oauth_account = config["oauthAccount"]
                if isinstance(oauth_account, dict):
                    email = oauth_account.get(
                        "emailAddress", oauth_account.get("email", "")
                    )
                    if email:
                        return True, f"Logged in as {email}"
                    return True, "OAuth account configured"
                elif oauth_account:
                    return True, "OAuth account configured"

            if "userID" in config and config["userID"]:
                return True, f"Authenticated (user: {config['userID'][:8]}...)"

            return False, "No OAuth account found in config"
        else:
            return False, "Claude config file not found (~/.claude.json)"
    except json.JSONDecodeError as e:
        return False, f"Error parsing Claude config: {e}"
    except Exception as e:
        return False, f"Error checking OAuth status: {e}"


def get_auth_mode() -> Tuple[AuthMode, str]:
    """Determine the current authentication mode for Claude Code."""
    has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    oauth_authenticated, oauth_message = check_claude_oauth_status()

    if oauth_authenticated:
        return "oauth", f"Claude Max (OAuth): {oauth_message}"
    elif has_api_key:
        return "api_key", "API Key: ANTHROPIC_API_KEY configured"
    else:
        return "none", "No authentication: Set ANTHROPIC_API_KEY or run 'claude login'"


def check_env_vars(logger: Optional[logging.Logger] = None) -> None:
    """Check that required environment variables and authentication are configured."""
    required_vars = ["CLAUDE_CODE_PATH"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = "Error: Missing required environment variables:"
        if logger:
            logger.error(error_msg)
            for var in missing_vars:
                logger.error(f"  - {var}")
        else:
            print(error_msg, file=sys.stderr)
            for var in missing_vars:
                print(f"  - {var}", file=sys.stderr)
        sys.exit(1)

    auth_mode, auth_message = get_auth_mode()

    if auth_mode == "none":
        error_msg = "Error: No Claude authentication configured."
        help_msg = """
To authenticate, use ONE of these methods:

1. Claude Max subscription (recommended — no API costs):
   $ claude login

2. API Key (usage-based billing):
   $ export ANTHROPIC_API_KEY='your-api-key-here'
"""
        if logger:
            logger.error(error_msg)
            logger.error(help_msg)
        else:
            print(error_msg, file=sys.stderr)
            print(help_msg, file=sys.stderr)
        sys.exit(1)
    else:
        if logger:
            logger.info(f"Authentication: {auth_message}")


def get_safe_subprocess_env() -> Dict[str, str]:
    """Get filtered environment variables safe for subprocess execution."""
    safe_env_vars = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GITHUB_PAT": os.getenv("GITHUB_PAT"),
        "CLAUDE_CODE_PATH": os.getenv("CLAUDE_CODE_PATH", "claude"),
        "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": os.getenv(
            "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR", "true"
        ),
        "HOME": os.getenv("HOME"),
        "USER": os.getenv("USER"),
        "PATH": os.getenv("PATH"),
        "SHELL": os.getenv("SHELL"),
        "TERM": os.getenv("TERM"),
        "LANG": os.getenv("LANG"),
        "LC_ALL": os.getenv("LC_ALL"),
        "PYTHONPATH": os.getenv("PYTHONPATH"),
        "PYTHONUNBUFFERED": "1",
        "PWD": os.getcwd(),
    }

    github_pat = os.getenv("GITHUB_PAT")
    if github_pat:
        safe_env_vars["GH_TOKEN"] = github_pat

    def _is_valid(v: str) -> bool:
        return v is not None and not (v.startswith("your_") and v.endswith("_here"))

    return {k: v for k, v in safe_env_vars.items() if _is_valid(v)}


def strip_markdown_code_formatting(text: str) -> str:
    """Strip markdown code formatting (backticks) from text."""
    if not text:
        return text

    result = text.strip()

    if result.startswith("```") and result.endswith("```"):
        result = result[3:]
        result = result[:-3]
        result = result.strip()
        if "\n" in result:
            lines = result.split("\n")
            first_line = lines[0].strip()
            if (
                first_line
                and len(first_line) < 20
                and " " not in first_line
                and "/" not in first_line
            ):
                result = "\n".join(lines[1:]).strip()

    if result.startswith("`") and result.endswith("`"):
        result = result[1:-1]

    return result.strip()
