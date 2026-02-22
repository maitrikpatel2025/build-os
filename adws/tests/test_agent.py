"""Tests for adws.adw_modules.agent — Agent execution and output parsing."""

import json
import os
from unittest.mock import patch

from adws.adw_modules.agent import (
    SLASH_COMMAND_MODEL_MAP,
    convert_jsonl_to_json,
    get_model_for_slash_command,
    parse_jsonl_output,
    save_prompt,
    truncate_output,
)
from adws.adw_modules.data_types import AgentTemplateRequest


class TestTruncateOutput:
    def test_short_text_unchanged(self):
        text = "Hello, world!"
        assert truncate_output(text) == text

    def test_long_text_truncated(self):
        text = "x" * 1000
        result = truncate_output(text, max_length=100)
        assert len(result) <= 120  # max_length + suffix length
        assert "truncated" in result

    def test_custom_suffix(self):
        text = "x" * 1000
        result = truncate_output(text, max_length=100, suffix="...")
        assert result.endswith("...")

    def test_jsonl_result_extraction(self):
        """Extracts result text from JSONL-style output."""
        lines = [
            '{"type": "assistant", "message": {"content": [{"text": "working..."}]}}',
            '{"type": "result", "result": "Build complete!"}',
        ]
        text = "\n".join(lines)
        result = truncate_output(text)
        assert result == "Build complete!"

    def test_jsonl_assistant_fallback(self):
        """Single-line JSONL without result type is not parsed as JSONL (needs \\n separator)."""
        lines = [
            '{"type": "assistant", "message": {"content": [{"text": "Done with task"}]}}',
        ]
        text = "\n".join(lines)
        # Single line starting with {"type": needs a second JSONL line to trigger extraction
        result = truncate_output(text)
        # With only one line, it doesn't match the multi-line JSONL detection
        assert "Done with task" in result

    def test_jsonl_with_many_messages(self):
        lines = ['{"type": "system", "data": "init"}']
        lines.append('{"type": "result", "result": "Final output"}')
        text = "\n".join(lines)
        result = truncate_output(text)
        assert result == "Final output"


class TestParseJsonlOutput:
    def test_parses_valid_jsonl(self, tmp_path):
        jsonl_file = str(tmp_path / "output.jsonl")
        lines = [
            json.dumps({"type": "system", "data": "init"}),
            json.dumps({"type": "assistant", "message": {"content": [{"text": "hello"}]}}),
            json.dumps({"type": "result", "result": "done", "session_id": "sess-123"}),
        ]
        with open(jsonl_file, "w") as f:
            f.write("\n".join(lines))

        messages, result = parse_jsonl_output(jsonl_file)
        assert len(messages) == 3
        assert result is not None
        assert result["type"] == "result"
        assert result["result"] == "done"
        assert result["session_id"] == "sess-123"

    def test_no_result_message(self, tmp_path):
        jsonl_file = str(tmp_path / "output.jsonl")
        with open(jsonl_file, "w") as f:
            f.write(json.dumps({"type": "system", "data": "init"}) + "\n")

        messages, result = parse_jsonl_output(jsonl_file)
        assert len(messages) == 1
        assert result is None

    def test_empty_file(self, tmp_path):
        jsonl_file = str(tmp_path / "output.jsonl")
        with open(jsonl_file, "w") as f:
            f.write("")

        messages, result = parse_jsonl_output(jsonl_file)
        assert messages == []
        assert result is None

    def test_nonexistent_file(self):
        messages, result = parse_jsonl_output("/nonexistent/file.jsonl")
        assert messages == []
        assert result is None


class TestConvertJsonlToJson:
    def test_converts_file(self, tmp_path):
        jsonl_file = str(tmp_path / "output.jsonl")
        lines = [
            json.dumps({"type": "system"}),
            json.dumps({"type": "result", "result": "ok"}),
        ]
        with open(jsonl_file, "w") as f:
            f.write("\n".join(lines))

        json_file = convert_jsonl_to_json(jsonl_file)
        assert json_file.endswith(".json")
        assert os.path.exists(json_file)

        with open(json_file) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 2


class TestSavePrompt:
    def test_saves_slash_command_prompt(self, tmp_path):
        with patch("adws.adw_modules.utils.get_project_root", return_value=str(tmp_path)):
            save_prompt("/build-os/init --arg1", "build001", "ops")

            prompt_file = tmp_path / "agents" / "build001" / "ops" / "prompts" / "build-os_init.txt"
            assert prompt_file.exists()
            assert prompt_file.read_text() == "/build-os/init --arg1"

    def test_ignores_non_slash_command(self, tmp_path):
        with patch("adws.adw_modules.utils.get_project_root", return_value=str(tmp_path)):
            save_prompt("Just a regular prompt", "build001", "ops")
            # No file should be created
            prompt_dir = tmp_path / "agents" / "build001" / "ops" / "prompts"
            assert not prompt_dir.exists()


class TestSlashCommandModelMap:
    def test_all_commands_mapped(self):
        expected_commands = [
            "/build-os/init",
            "/build-os/scaffold",
            "/build-os/build-shell",
            "/build-os/build-section",
            "/build-os/build-api",
            "/build-os/wire-data",
            "/build-os/validate",
            "/build-os/build-all",
            "/build-os/finalize",
            "/build-os/status",
            "/build-os/resume",
        ]
        for cmd in expected_commands:
            assert cmd in SLASH_COMMAND_MODEL_MAP

    def test_each_has_base_and_heavy(self):
        for cmd, config in SLASH_COMMAND_MODEL_MAP.items():
            assert "base" in config, f"{cmd} missing 'base' model"
            assert "heavy" in config, f"{cmd} missing 'heavy' model"

    def test_models_are_valid(self):
        valid_models = {"sonnet", "opus"}
        for cmd, config in SLASH_COMMAND_MODEL_MAP.items():
            for model_set, model in config.items():
                assert model in valid_models, f"{cmd}[{model_set}] = {model} is invalid"


class TestGetModelForSlashCommand:
    def test_returns_base_model_when_no_state(self, tmp_path):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            req = AgentTemplateRequest(
                agent_name="ops",
                slash_command="/build-os/init",
                build_id="nonexistent",
            )
            model = get_model_for_slash_command(req)
            assert model == "sonnet"  # base model for init
