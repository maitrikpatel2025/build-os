"""Tests for adws.adw_modules.scaffold_ops — Project scaffolding."""

import json
import os
from unittest.mock import patch

from adws.adw_modules.data_types import DesignSystem, TechStack
from adws.adw_modules.scaffold_ops import _create_directory_structure, scaffold_project


class TestScaffoldProject:
    def test_creates_output_directory(self, tmp_path, logger):
        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(tmp_path)):
            output_path, error = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=["dashboard"],
                logger=logger,
            )
            assert error is None
            assert output_path is not None
            assert os.path.exists(output_path)

    def test_output_path_uses_slug(self, tmp_path, logger):
        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(tmp_path)):
            output_path, _ = scaffold_project(
                product_name="My Awesome App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=[],
                logger=logger,
            )
            assert "my-awesome-app" in output_path

    def test_existing_directory_returns_early(self, tmp_path, logger):
        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(tmp_path)):
            output_dir = tmp_path / "output" / "test-app"
            output_dir.mkdir(parents=True)

            output_path, error = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=[],
                logger=logger,
            )
            assert error is None
            assert output_path == str(output_dir)

    def test_creates_frontend_structure(self, tmp_path, logger):
        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(tmp_path)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=["dashboard"],
                logger=logger,
            )
            client_dir = os.path.join(output_path, "app", "client")
            assert os.path.exists(client_dir)
            assert os.path.exists(os.path.join(client_dir, "src"))

    def test_creates_backend_structure(self, tmp_path, logger):
        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(tmp_path)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=["dashboard"],
                logger=logger,
            )
            server_dir = os.path.join(output_path, "app", "server")
            assert os.path.exists(server_dir)
            assert os.path.exists(os.path.join(server_dir, "routes"))
            assert os.path.exists(os.path.join(server_dir, "models"))
            assert os.path.exists(os.path.join(server_dir, "core"))

    def test_creates_scripts(self, tmp_path, logger):
        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(tmp_path)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=[],
                logger=logger,
            )
            assert os.path.exists(os.path.join(output_path, "scripts", "start.sh"))
            assert os.path.exists(os.path.join(output_path, "scripts", "stop.sh"))

    def test_creates_config_files(self, tmp_path, logger):
        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(tmp_path)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=[],
                logger=logger,
            )
            assert os.path.exists(os.path.join(output_path, "README.md"))
            assert os.path.exists(os.path.join(output_path, ".gitignore"))
            assert os.path.exists(os.path.join(output_path, ".ports.env"))


class TestCreateDirectoryStructure:
    def test_creates_base_dirs(self, tmp_path, logger):
        output_path = str(tmp_path / "project")
        os.makedirs(output_path)
        _create_directory_structure(output_path, [], logger)

        assert os.path.isdir(os.path.join(output_path, "app", "client", "src", "components"))
        assert os.path.isdir(os.path.join(output_path, "app", "client", "src", "shell"))
        assert os.path.isdir(os.path.join(output_path, "app", "client", "src", "api"))
        assert os.path.isdir(os.path.join(output_path, "app", "server", "routes"))
        assert os.path.isdir(os.path.join(output_path, "app", "server", "models"))

    def test_creates_section_dirs(self, tmp_path, logger):
        output_path = str(tmp_path / "project")
        os.makedirs(output_path)
        _create_directory_structure(output_path, ["dashboard", "settings"], logger)

        assert os.path.isdir(os.path.join(output_path, "app", "client", "src", "sections", "dashboard"))
        assert os.path.isdir(os.path.join(output_path, "app", "client", "src", "sections", "settings"))


class TestScaffoldWithoutTemplates:
    """Test scaffolding when no template directory exists (generates files directly)."""

    def test_generates_frontend_files(self, tmp_path, logger):
        # Use a project root with no templates/ directory
        project_root = tmp_path / "no-templates"
        project_root.mkdir()

        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(project_root)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=["dashboard"],
                logger=logger,
            )
            client_dir = os.path.join(output_path, "app", "client")

            # Check generated files
            assert os.path.exists(os.path.join(client_dir, "package.json"))
            assert os.path.exists(os.path.join(client_dir, "vite.config.js"))
            assert os.path.exists(os.path.join(client_dir, "tailwind.config.js"))
            assert os.path.exists(os.path.join(client_dir, "index.html"))
            assert os.path.exists(os.path.join(client_dir, "src", "main.jsx"))
            assert os.path.exists(os.path.join(client_dir, "src", "index.css"))
            assert os.path.exists(os.path.join(client_dir, "src", "App.jsx"))

    def test_generated_package_json_valid(self, tmp_path, logger):
        project_root = tmp_path / "no-templates"
        project_root.mkdir()

        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(project_root)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=[],
                logger=logger,
            )
            pkg_path = os.path.join(output_path, "app", "client", "package.json")
            with open(pkg_path) as f:
                pkg = json.load(f)
            assert "react" in pkg["dependencies"]
            assert pkg["name"] == "test-app-client"

    def test_generates_backend_files(self, tmp_path, logger):
        project_root = tmp_path / "no-templates"
        project_root.mkdir()

        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(project_root)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=[],
                logger=logger,
            )
            server_dir = os.path.join(output_path, "app", "server")
            assert os.path.exists(os.path.join(server_dir, "server.py"))
            assert os.path.exists(os.path.join(server_dir, "pyproject.toml"))
            assert os.path.exists(os.path.join(server_dir, "core", "database.py"))
            assert os.path.exists(os.path.join(server_dir, "tests", "conftest.py"))

    def test_app_jsx_contains_section_routes(self, tmp_path, logger):
        project_root = tmp_path / "no-templates"
        project_root.mkdir()

        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(project_root)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=["dashboard", "settings"],
                logger=logger,
            )
            app_jsx = os.path.join(output_path, "app", "client", "src", "App.jsx")
            with open(app_jsx) as f:
                content = f.read()
            assert "/dashboard" in content
            assert "/settings" in content

    def test_start_script_is_executable(self, tmp_path, logger):
        project_root = tmp_path / "no-templates"
        project_root.mkdir()

        with patch("adws.adw_modules.scaffold_ops.get_project_root", return_value=str(project_root)):
            output_path, _ = scaffold_project(
                product_name="Test App",
                tech_stack=TechStack(),
                design_system=DesignSystem(),
                sections=[],
                logger=logger,
            )
            start_sh = os.path.join(output_path, "scripts", "start.sh")
            assert os.access(start_sh, os.X_OK)
