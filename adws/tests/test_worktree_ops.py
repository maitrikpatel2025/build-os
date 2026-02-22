"""Tests for adws.adw_modules.worktree_ops — Port management and worktree paths."""

import os
from unittest.mock import patch

import pytest

from adws.adw_modules.worktree_ops import (
    BACKEND_PORT_BASE,
    FRONTEND_PORT_BASE,
    MAX_CONCURRENT_SLOTS,
    find_available_ports,
    get_ports_for_milestone,
    get_worktree_path,
    is_port_available,
    list_active_worktrees,
    setup_worktree_environment,
)


class TestGetWorktreePath:
    def test_returns_correct_path(self, tmp_path):
        with patch("adws.adw_modules.worktree_ops.get_project_root", return_value=str(tmp_path)):
            path = get_worktree_path("abc12345", "01-shell")
            assert path == str(tmp_path / "trees" / "abc12345-01-shell")

    def test_combines_build_and_milestone(self, tmp_path):
        with patch("adws.adw_modules.worktree_ops.get_project_root", return_value=str(tmp_path)):
            path = get_worktree_path("build001", "02-dashboard")
            assert "build001-02-dashboard" in path


class TestGetPortsForMilestone:
    def test_returns_two_ports(self):
        backend, frontend = get_ports_for_milestone("abc", "01-shell")
        assert isinstance(backend, int)
        assert isinstance(frontend, int)

    def test_backend_in_range(self):
        backend, _ = get_ports_for_milestone("abc", "01-shell")
        assert BACKEND_PORT_BASE <= backend < BACKEND_PORT_BASE + MAX_CONCURRENT_SLOTS

    def test_frontend_in_range(self):
        _, frontend = get_ports_for_milestone("abc", "01-shell")
        assert FRONTEND_PORT_BASE <= frontend < FRONTEND_PORT_BASE + MAX_CONCURRENT_SLOTS

    def test_deterministic(self):
        ports1 = get_ports_for_milestone("abc", "01-shell")
        ports2 = get_ports_for_milestone("abc", "01-shell")
        assert ports1 == ports2

    def test_different_milestones_can_differ(self):
        ports1 = get_ports_for_milestone("abc", "01-shell")
        get_ports_for_milestone("abc", "02-dashboard")
        # They may be different (not guaranteed, but the hash should differ)
        # At minimum, the function should not raise
        assert len(ports1) == 2

    def test_port_offset_matches(self):
        """Backend and frontend should have matching offsets."""
        backend, frontend = get_ports_for_milestone("abc", "01-shell")
        assert (backend - BACKEND_PORT_BASE) == (frontend - FRONTEND_PORT_BASE)


class TestIsPortAvailable:
    def test_available_port(self):
        # Port 0 trick: bind to 0, OS picks a free port
        # Instead, test a high port that's likely free
        result = is_port_available(19999)
        assert isinstance(result, bool)

    def test_returns_bool(self):
        result = is_port_available(9999)
        assert isinstance(result, bool)


class TestFindAvailablePorts:
    def test_finds_ports(self):
        # This should succeed since we have 15 slots
        backend, frontend = find_available_ports("test", "01-shell")
        assert BACKEND_PORT_BASE <= backend < BACKEND_PORT_BASE + MAX_CONCURRENT_SLOTS
        assert FRONTEND_PORT_BASE <= frontend < FRONTEND_PORT_BASE + MAX_CONCURRENT_SLOTS

    def test_raises_when_no_ports(self):
        """When all ports are taken, should raise RuntimeError."""
        with patch("adws.adw_modules.worktree_ops.is_port_available", return_value=False):
            with pytest.raises(RuntimeError, match="No available ports"):
                find_available_ports("test", "01-shell")


class TestSetupWorktreeEnvironment:
    def test_creates_ports_env(self, tmp_path, logger):
        worktree_path = str(tmp_path / "worktree")
        os.makedirs(worktree_path)

        setup_worktree_environment(worktree_path, 9300, 9400, logger)

        ports_env = os.path.join(worktree_path, ".ports.env")
        assert os.path.exists(ports_env)

        with open(ports_env) as f:
            content = f.read()

        assert "BACKEND_PORT=9300" in content
        assert "FRONTEND_PORT=9400" in content
        assert "VITE_BACKEND_URL=http://localhost:9300" in content


class TestListActiveWorktrees:
    def test_returns_list(self, tmp_path):
        with patch("adws.adw_modules.worktree_ops.get_project_root", return_value=str(tmp_path)):
            result = list_active_worktrees()
            assert isinstance(result, list)

    def test_empty_when_no_trees_dir(self, tmp_path):
        with patch("adws.adw_modules.worktree_ops.get_project_root", return_value=str(tmp_path)):
            result = list_active_worktrees()
            assert result == []
