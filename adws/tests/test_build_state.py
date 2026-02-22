"""Tests for adws.adw_modules.build_state — BuildState class."""

from unittest.mock import patch

import pytest

from adws.adw_modules.build_state import BuildState


class TestBuildStateInit:
    def test_requires_build_id(self):
        with pytest.raises(ValueError, match="build_id is required"):
            BuildState("")

    def test_empty_string_rejected(self):
        with pytest.raises(ValueError):
            BuildState("")

    def test_creates_with_valid_id(self, build_id):
        state = BuildState(build_id)
        assert state.build_id == build_id
        assert state.data["build_id"] == build_id


class TestBuildStateUpdate:
    def test_update_sets_key(self, build_id):
        state = BuildState(build_id)
        state.update(product_name="My App")
        assert state.data["product_name"] == "My App"

    def test_update_sets_updated_at(self, build_id):
        state = BuildState(build_id)
        state.update(product_name="My App")
        assert "updated_at" in state.data

    def test_update_multiple_keys(self, build_id):
        state = BuildState(build_id)
        state.update(product_name="My App", model_set="heavy")
        assert state.data["product_name"] == "My App"
        assert state.data["model_set"] == "heavy"


class TestBuildStateGet:
    def test_get_existing_key(self, build_id):
        state = BuildState(build_id)
        state.update(product_name="My App")
        assert state.get("product_name") == "My App"

    def test_get_missing_key_returns_default(self, build_id):
        state = BuildState(build_id)
        assert state.get("missing_key") is None
        assert state.get("missing_key", "fallback") == "fallback"


class TestBuildStateMilestones:
    def test_get_milestones_empty(self, build_id):
        state = BuildState(build_id)
        assert state.get_milestones() == []

    def test_get_milestones(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        milestones = state.get_milestones()
        assert len(milestones) == 2
        assert milestones[0]["id"] == "01-shell"

    def test_get_milestone_by_id(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        m = state.get_milestone("02-dashboard")
        assert m is not None
        assert m["name"] == "Dashboard"

    def test_get_milestone_not_found(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        assert state.get_milestone("nonexistent") is None

    def test_update_milestone(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        result = state.update_milestone("01-shell", status="in_progress", backend_port=9300)
        assert result is True
        m = state.get_milestone("01-shell")
        assert m["status"] == "in_progress"
        assert m["backend_port"] == 9300

    def test_update_milestone_not_found(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        result = state.update_milestone("nonexistent", status="complete")
        assert result is False


class TestBuildStateCurrentMilestone:
    def test_no_current_milestone(self, build_id):
        state = BuildState(build_id)
        assert state.get_current_milestone() is None

    def test_set_and_get_current(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        state.set_current_milestone("01-shell")
        current = state.get_current_milestone()
        assert current is not None
        assert current["id"] == "01-shell"

    def test_get_next_pending(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        next_m = state.get_next_pending_milestone()
        assert next_m["id"] == "01-shell"

    def test_get_next_pending_skips_complete(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        state.update_milestone("01-shell", status="complete")
        next_m = state.get_next_pending_milestone()
        assert next_m["id"] == "02-dashboard"

    def test_get_next_pending_returns_none_when_all_complete(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        state.update_milestone("01-shell", status="complete")
        state.update_milestone("02-dashboard", status="complete")
        assert state.get_next_pending_milestone() is None


class TestBuildStateCost:
    def test_add_cost(self, build_id):
        state = BuildState(build_id)
        state.add_cost(0.05)
        assert state.data["total_cost"] == 0.05

    def test_add_cost_accumulates(self, build_id):
        state = BuildState(build_id)
        state.add_cost(0.05)
        state.add_cost(0.10)
        assert abs(state.data["total_cost"] - 0.15) < 1e-9


class TestBuildStatePersistence:
    def test_save_and_load(self, build_id, sample_build_state_data, tmp_path):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            state = BuildState(build_id)
            state.data = sample_build_state_data.copy()
            state.save()

            loaded = BuildState.load(build_id)
            assert loaded is not None
            assert loaded.build_id == build_id
            assert loaded.get("product_name") == "Test App"
            assert len(loaded.get_milestones()) == 2

    def test_load_nonexistent(self, tmp_path):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            loaded = BuildState.load("nonexistent")
            assert loaded is None

    def test_save_creates_directories(self, build_id, sample_build_state_data, tmp_path):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            state = BuildState(build_id)
            state.data = sample_build_state_data.copy()
            state.save()

            state_dir = tmp_path / "agents" / build_id
            assert state_dir.exists()
            assert (state_dir / "build_state.json").exists()

    def test_save_validates_with_pydantic(self, build_id, tmp_path):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            state = BuildState(build_id)
            # Missing required product_name
            with pytest.raises(Exception):
                state.save()

    def test_get_state_path(self, build_id, tmp_path):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            state = BuildState(build_id)
            path = state.get_state_path()
            assert path.endswith("build_state.json")
            assert build_id in path

    def test_get_output_path(self, build_id, sample_build_state_data):
        state = BuildState(build_id)
        state.data = sample_build_state_data
        assert state.get_output_path() is None

        state.update(output_path="/tmp/output/my-app")
        assert state.get_output_path() == "/tmp/output/my-app"


class TestBuildStateFindLatest:
    def test_find_latest_no_agents_dir(self, tmp_path):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            assert BuildState.find_latest() is None

    def test_find_latest_single_build(self, build_id, sample_build_state_data, tmp_path):
        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            state = BuildState(build_id)
            state.data = sample_build_state_data.copy()
            state.save()

            latest = BuildState.find_latest()
            assert latest is not None
            assert latest.build_id == build_id

    def test_find_latest_multiple_builds(self, sample_build_state_data, tmp_path):
        import time

        with patch("adws.adw_modules.build_state.get_project_root", return_value=str(tmp_path)):
            # First build
            state1 = BuildState("build001")
            data1 = sample_build_state_data.copy()
            data1["build_id"] = "build001"
            state1.data = data1
            state1.save()

            time.sleep(0.1)

            # Second build (newer)
            state2 = BuildState("build002")
            data2 = sample_build_state_data.copy()
            data2["build_id"] = "build002"
            state2.data = data2
            state2.save()

            latest = BuildState.find_latest()
            assert latest is not None
            assert latest.build_id == "build002"
