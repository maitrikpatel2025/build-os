"""Tests for adws.adw_modules.utils — Utility functions."""

import json
import os
from unittest.mock import patch

import pytest

from adws.adw_modules.utils import (
    check_claude_oauth_status,
    get_auth_mode,
    get_project_root,
    get_safe_subprocess_env,
    make_build_id,
    parse_json,
    strip_markdown_code_formatting,
)


class TestGetProjectRoot:
    def test_returns_string(self):
        root = get_project_root()
        assert isinstance(root, str)

    def test_is_absolute_path(self):
        root = get_project_root()
        assert os.path.isabs(root)

    def test_ends_at_build_os(self):
        root = get_project_root()
        assert root.endswith("build-os")


class TestMakeBuildId:
    def test_returns_8_chars(self):
        bid = make_build_id()
        assert len(bid) == 8

    def test_unique_ids(self):
        ids = {make_build_id() for _ in range(100)}
        assert len(ids) == 100

    def test_is_string(self):
        bid = make_build_id()
        assert isinstance(bid, str)


class TestParseJson:
    def test_plain_json_object(self):
        result = parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_plain_json_array(self):
        result = parse_json('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_json_in_code_block(self):
        text = '```json\n{"key": "value"}\n```'
        result = parse_json(text)
        assert result == {"key": "value"}

    def test_json_in_generic_code_block(self):
        text = '```\n{"key": "value"}\n```'
        result = parse_json(text)
        assert result == {"key": "value"}

    def test_json_with_surrounding_text(self):
        text = 'Here is the result:\n{"key": "value"}\nDone!'
        result = parse_json(text)
        assert result == {"key": "value"}

    def test_array_with_surrounding_text(self):
        text = 'Output: [1, 2, 3] end'
        result = parse_json(text)
        assert result == [1, 2, 3]

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parse_json("not json at all")

    def test_with_pydantic_target(self):
        from adws.adw_modules.data_types import TechStack
        text = '{"frontend": "react-vite", "backend": "fastapi", "styling": "tailwind", "database": "sqlite"}'
        result = parse_json(text, TechStack)
        assert isinstance(result, TechStack)
        assert result.frontend == "react-vite"

    def test_nested_json_object(self):
        text = '{"a": {"b": [1, 2]}}'
        result = parse_json(text)
        assert result["a"]["b"] == [1, 2]


class TestStripMarkdownCodeFormatting:
    def test_plain_text_unchanged(self):
        assert strip_markdown_code_formatting("hello") == "hello"

    def test_empty_string(self):
        assert strip_markdown_code_formatting("") == ""

    def test_none_returns_none(self):
        assert strip_markdown_code_formatting(None) is None

    def test_single_backticks(self):
        assert strip_markdown_code_formatting("`code`") == "code"

    def test_triple_backticks_with_lang(self):
        text = "```python\nprint('hello')\n```"
        result = strip_markdown_code_formatting(text)
        assert result == "print('hello')"

    def test_triple_backticks_without_lang(self):
        text = "```\nsome code\n```"
        result = strip_markdown_code_formatting(text)
        assert result == "some code"


class TestGetSafeSubprocessEnv:
    def test_returns_dict(self):
        env = get_safe_subprocess_env()
        assert isinstance(env, dict)

    def test_includes_path(self):
        env = get_safe_subprocess_env()
        assert "PATH" in env

    def test_includes_home(self):
        env = get_safe_subprocess_env()
        assert "HOME" in env

    def test_sets_pythonunbuffered(self):
        env = get_safe_subprocess_env()
        assert env.get("PYTHONUNBUFFERED") == "1"

    def test_filters_placeholder_values(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "your_key_here"}):
            env = get_safe_subprocess_env()
            assert "ANTHROPIC_API_KEY" not in env

    def test_includes_valid_api_key(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-real-key"}):
            env = get_safe_subprocess_env()
            assert env.get("ANTHROPIC_API_KEY") == "sk-ant-real-key"

    def test_github_pat_sets_gh_token(self):
        with patch.dict(os.environ, {"GITHUB_PAT": "ghp_abc123"}):
            env = get_safe_subprocess_env()
            assert env.get("GH_TOKEN") == "ghp_abc123"


class TestCheckClaudeOAuthStatus:
    def test_no_config_file(self, tmp_path):
        with patch("adws.adw_modules.utils.os.path.expanduser", return_value=str(tmp_path / "nope.json")):
            ok, msg = check_claude_oauth_status()
            assert not ok
            assert "not found" in msg

    def test_with_oauth_account(self, tmp_path):
        config_path = tmp_path / ".claude.json"
        config_path.write_text(json.dumps({
            "oauthAccount": {"emailAddress": "test@example.com"}
        }))
        with patch("adws.adw_modules.utils.os.path.expanduser", return_value=str(config_path)):
            ok, msg = check_claude_oauth_status()
            assert ok
            assert "test@example.com" in msg

    def test_with_user_id(self, tmp_path):
        config_path = tmp_path / ".claude.json"
        config_path.write_text(json.dumps({"userID": "user_abcdef12345"}))
        with patch("adws.adw_modules.utils.os.path.expanduser", return_value=str(config_path)):
            ok, msg = check_claude_oauth_status()
            assert ok
            assert "Authenticated" in msg

    def test_empty_config(self, tmp_path):
        config_path = tmp_path / ".claude.json"
        config_path.write_text("{}")
        with patch("adws.adw_modules.utils.os.path.expanduser", return_value=str(config_path)):
            ok, msg = check_claude_oauth_status()
            assert not ok


class TestGetAuthMode:
    def test_oauth_mode(self):
        with patch("adws.adw_modules.utils.check_claude_oauth_status", return_value=(True, "logged in")):
            mode, msg = get_auth_mode()
            assert mode == "oauth"

    def test_api_key_mode(self):
        with patch("adws.adw_modules.utils.check_claude_oauth_status", return_value=(False, "no oauth")):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-real"}):
                mode, msg = get_auth_mode()
                assert mode == "api_key"

    def test_no_auth(self):
        with patch("adws.adw_modules.utils.check_claude_oauth_status", return_value=(False, "none")):
            with patch.dict(os.environ, {}, clear=True):
                # Need to ensure ANTHROPIC_API_KEY is not set
                env = os.environ.copy()
                env.pop("ANTHROPIC_API_KEY", None)
                with patch.dict(os.environ, env, clear=True):
                    mode, msg = get_auth_mode()
                    assert mode == "none"
