"""Tests for adws.adw_modules.milestone_ops — Milestone coordination."""

from unittest.mock import patch

from adws.adw_modules.build_state import BuildState
from adws.adw_modules.milestone_ops import (
    advance_milestone_status,
    get_milestone_summary,
)


class TestAdvanceMilestoneStatus:
    def test_advances_status(self, build_id, sample_build_state_data, tmp_path, logger):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            state = BuildState(build_id)
            state.data = sample_build_state_data.copy()
            state.data["product_name"] = "Test App"

            advance_milestone_status(state, "01-shell", "in_progress", logger)

            m = state.get_milestone("01-shell")
            assert m["status"] == "in_progress"

    def test_saves_state(self, build_id, sample_build_state_data, tmp_path, logger):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            state = BuildState(build_id)
            state.data = sample_build_state_data.copy()

            advance_milestone_status(state, "01-shell", "frontend_done", logger)

            # Verify state was saved
            loaded = BuildState.load(build_id)
            assert loaded is not None
            m = loaded.get_milestone("01-shell")
            assert m["status"] == "frontend_done"


class TestGetMilestoneSummary:
    def test_empty_milestones(self, build_id):
        state = BuildState(build_id)
        summary = get_milestone_summary(state)
        assert "No milestones found" in summary

    def test_includes_build_id(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        summary = get_milestone_summary(state)
        assert build_id in summary

    def test_includes_product_name(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        summary = get_milestone_summary(state)
        assert "Test App" in summary

    def test_shows_all_milestones(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        summary = get_milestone_summary(state)
        assert "01-shell" in summary
        assert "02-dashboard" in summary

    def test_shows_progress_count(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        summary = get_milestone_summary(state)
        assert "0/2 milestones complete" in summary

    def test_shows_complete_count(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        state.update_milestone("01-shell", status="complete")
        summary = get_milestone_summary(state)
        assert "1/2 milestones complete" in summary

    def test_shows_status_icons(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        state.update_milestone("01-shell", status="complete")
        summary = get_milestone_summary(state)
        assert "[x]" in summary  # complete
        assert "[ ]" in summary  # pending

    def test_shows_port_info(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        state.update_milestone("01-shell", backend_port=9300, frontend_port=9400)
        summary = get_milestone_summary(state)
        assert "9300" in summary
        assert "9400" in summary

    def test_shows_cost_when_nonzero(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        state.data["total_cost"] = 1.2345
        summary = get_milestone_summary(state)
        assert "$1.2345" in summary

    def test_hides_cost_when_zero(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        summary = get_milestone_summary(state)
        assert "Total cost" not in summary
