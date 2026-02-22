"""Tests for adws.adw_modules.e2e_ops — E2E test orchestrator."""

import json
from unittest.mock import MagicMock, patch

from adws.adw_modules.data_types import (
    BuildMilestone,
    BuildStateData,
    E2ETestResult,
    E2ETestStep,
)
from adws.adw_modules.e2e_ops import (
    parse_e2e_test_results,
    run_e2e_with_resolution,
)

# --- E2ETestStep model ---


class TestE2ETestStep:
    def test_passed_step(self):
        step = E2ETestStep(step="Step 1: Navigate", passed=True)
        assert step.passed is True
        assert step.error is None

    def test_failed_step(self):
        step = E2ETestStep(step="Step 2: Click button", passed=False, error="Element not found")
        assert step.passed is False
        assert step.error == "Element not found"

    def test_error_defaults_to_none(self):
        step = E2ETestStep(step="Step 1: Load", passed=True)
        assert step.error is None


# --- E2ETestResult model ---


class TestE2ETestResult:
    def test_passed_result(self, e2e_passed_json):
        result = E2ETestResult(**e2e_passed_json)
        assert result.status == "passed"
        assert result.test_name == "E2E: Dashboard"
        assert len(result.steps) == 2
        assert all(s.passed for s in result.steps)

    def test_failed_result(self, e2e_failed_json):
        result = E2ETestResult(**e2e_failed_json)
        assert result.status == "failed"
        assert result.error is not None
        assert not result.steps[1].passed

    def test_minimal_result(self):
        result = E2ETestResult(
            test_name="E2E: Settings",
            test_path="agents/x/e2e/settings/test_settings.md",
            status="passed",
        )
        assert result.screenshots == []
        assert result.steps == []
        assert result.error is None

    def test_invalid_status_rejected(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            E2ETestResult(
                test_name="Test",
                test_path="path",
                status="unknown",
            )

    def test_model_dump_round_trip(self, e2e_passed_json):
        result = E2ETestResult(**e2e_passed_json)
        dumped = result.model_dump()
        result2 = E2ETestResult(**dumped)
        assert result2.test_name == result.test_name
        assert result2.status == result.status
        assert len(result2.steps) == len(result.steps)


# --- parse_e2e_test_results ---


class TestParseE2ETestResults:
    def test_valid_json(self, e2e_passed_json):
        raw = json.dumps(e2e_passed_json)
        result = parse_e2e_test_results(raw)
        assert result is not None
        assert result.status == "passed"
        assert result.test_name == "E2E: Dashboard"

    def test_json_in_code_block(self, e2e_failed_json):
        raw = f"Here are the results:\n```json\n{json.dumps(e2e_failed_json)}\n```\nDone."
        result = parse_e2e_test_results(raw)
        assert result is not None
        assert result.status == "failed"

    def test_json_with_surrounding_text(self, e2e_passed_json):
        raw = f"The test completed successfully.\n{json.dumps(e2e_passed_json)}\nAll done."
        result = parse_e2e_test_results(raw)
        assert result is not None
        assert result.status == "passed"

    def test_empty_string(self):
        assert parse_e2e_test_results("") is None

    def test_none_like(self):
        assert parse_e2e_test_results("   ") is None

    def test_invalid_json(self):
        assert parse_e2e_test_results("not json at all") is None

    def test_valid_json_but_wrong_schema(self):
        assert parse_e2e_test_results('{"foo": "bar"}') is None

    def test_json_missing_required_fields(self):
        # Has test_name but no status
        assert parse_e2e_test_results('{"test_name": "Test"}') is None


# --- BuildStateData.e2e_enabled ---


class TestBuildStateDataE2E:
    def test_e2e_enabled_default_true(self):
        bsd = BuildStateData(build_id="test123", product_name="App")
        assert bsd.e2e_enabled is True

    def test_e2e_enabled_override_false(self):
        bsd = BuildStateData(build_id="test123", product_name="App", e2e_enabled=False)
        assert bsd.e2e_enabled is False

    def test_e2e_enabled_in_dump(self):
        bsd = BuildStateData(build_id="test123", product_name="App", e2e_enabled=False)
        dumped = bsd.model_dump()
        assert dumped["e2e_enabled"] is False


# --- BuildMilestone e2e fields ---


class TestBuildMilestoneE2E:
    def test_e2e_fields_default_none(self):
        m = BuildMilestone(id="02-dashboard", name="Dashboard")
        assert m.e2e_test_status is None
        assert m.e2e_test_results is None

    def test_e2e_fields_set(self, e2e_passed_json):
        result = E2ETestResult(**e2e_passed_json)
        m = BuildMilestone(
            id="02-dashboard",
            name="Dashboard",
            e2e_test_status="complete",
            e2e_test_results=result,
        )
        assert m.e2e_test_status == "complete"
        assert m.e2e_test_results.status == "passed"

    def test_e2e_fields_round_trip(self, e2e_failed_json):
        result = E2ETestResult(**e2e_failed_json)
        m = BuildMilestone(
            id="02-dashboard",
            name="Dashboard",
            e2e_test_status="failed",
            e2e_test_results=result,
        )
        dumped = m.model_dump()
        m2 = BuildMilestone(**dumped)
        assert m2.e2e_test_status == "failed"
        assert m2.e2e_test_results.status == "failed"


# --- run_e2e_with_resolution retry logic ---


class TestRunE2EWithResolution:
    def _make_mock_state(self):
        state = MagicMock()
        state.build_id = "test123"
        state.get.return_value = True
        return state

    @patch("adws.adw_modules.e2e_ops.execute_template")
    def test_passes_on_first_try(self, mock_exec, e2e_passed_json, logger):
        mock_exec.return_value = MagicMock(
            success=True, output=json.dumps(e2e_passed_json)
        )
        state = self._make_mock_state()

        result = run_e2e_with_resolution(state, "02-dashboard", "dashboard", "/tmp", logger)

        assert result is not None
        assert result.status == "passed"
        assert mock_exec.call_count == 1

    @patch("adws.adw_modules.e2e_ops.resolve_e2e_failure")
    @patch("adws.adw_modules.e2e_ops.execute_template")
    def test_retries_on_failure_then_passes(self, mock_exec, mock_resolve, e2e_failed_json, e2e_passed_json, logger):
        # First call fails, second call (after resolution) passes
        mock_exec.side_effect = [
            MagicMock(success=True, output=json.dumps(e2e_failed_json)),
            MagicMock(success=True, output=json.dumps(e2e_passed_json)),
        ]
        mock_resolve.return_value = True
        state = self._make_mock_state()

        result = run_e2e_with_resolution(state, "02-dashboard", "dashboard", "/tmp", logger)

        assert result is not None
        assert result.status == "passed"
        assert mock_exec.call_count == 2
        assert mock_resolve.call_count == 1

    @patch("adws.adw_modules.e2e_ops.resolve_e2e_failure")
    @patch("adws.adw_modules.e2e_ops.execute_template")
    def test_exhausts_retries(self, mock_exec, mock_resolve, e2e_failed_json, logger):
        # All calls fail
        mock_exec.return_value = MagicMock(
            success=True, output=json.dumps(e2e_failed_json)
        )
        mock_resolve.return_value = True
        state = self._make_mock_state()

        result = run_e2e_with_resolution(state, "02-dashboard", "dashboard", "/tmp", logger, max_retries=2)

        assert result is not None
        assert result.status == "failed"
        # 1 initial + 2 retries = 3 total
        assert mock_exec.call_count == 3
        assert mock_resolve.call_count == 2

    @patch("adws.adw_modules.e2e_ops.execute_template")
    def test_returns_none_on_execution_failure(self, mock_exec, logger):
        mock_exec.return_value = MagicMock(success=False, output="Agent error")
        state = self._make_mock_state()

        result = run_e2e_with_resolution(state, "02-dashboard", "dashboard", "/tmp", logger)

        assert result is None
