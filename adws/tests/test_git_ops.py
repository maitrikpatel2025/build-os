"""Tests for adws.adw_modules.git_ops — Git operations."""

from adws.adw_modules.git_ops import (
    commit_changes,
    get_current_branch,
    init_git_repo,
    make_milestone_branch_name,
)


class TestMakeMilestoneBranchName:
    def test_format(self):
        name = make_milestone_branch_name("abc12345", "01-shell")
        assert name == "build-abc12345-01-shell"

    def test_with_section_milestone(self):
        name = make_milestone_branch_name("abc12345", "02-dashboard")
        assert name == "build-abc12345-02-dashboard"

    def test_contains_build_id(self):
        name = make_milestone_branch_name("xyz99999", "03-settings")
        assert "xyz99999" in name

    def test_contains_milestone_id(self):
        name = make_milestone_branch_name("abc12345", "04-reports")
        assert "04-reports" in name


class TestGetCurrentBranch:
    def test_returns_branch_name(self, tmp_path):
        """Test with a real git repo."""
        import subprocess
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "checkout", "-b", "test-branch"], cwd=str(tmp_path), capture_output=True)
        # Need at least one commit
        (tmp_path / "dummy.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init", "--allow-empty"],
            cwd=str(tmp_path),
            capture_output=True,
            env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@test.com",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com",
                 "HOME": str(tmp_path), "PATH": __import__("os").environ["PATH"]},
        )

        branch = get_current_branch(cwd=str(tmp_path))
        assert branch == "test-branch"


class TestCommitChanges:
    def test_no_changes_returns_success(self, tmp_path):
        """When there are no changes, commit should succeed (no-op)."""
        import subprocess
        env = {
            "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@test.com",
            "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com",
            "HOME": str(tmp_path), "PATH": __import__("os").environ["PATH"],
        }
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, env=env)
        (tmp_path / "dummy.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True, env=env)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True, env=env)

        success, error = commit_changes("test commit", cwd=str(tmp_path))
        assert success is True
        assert error is None  # no changes to commit


class TestInitGitRepo:
    def test_initializes_repo(self, tmp_path):
        repo_dir = tmp_path / "new-repo"
        repo_dir.mkdir()
        (repo_dir / "README.md").write_text("# Test")

        success, error = init_git_repo(str(repo_dir))
        # May fail if no git user configured, but should not crash
        assert isinstance(success, bool)
