"""Shared fixtures for Build OS tests."""

import logging

import pytest


@pytest.fixture
def build_id():
    return "a1b2c3d4"


@pytest.fixture
def logger():
    return logging.getLogger("test")


@pytest.fixture
def sample_build_state_data(build_id):
    return {
        "build_id": build_id,
        "product_name": "Test App",
        "product_plan_path": "product-plan/",
        "tech_stack": {
            "frontend": "react-vite",
            "backend": "fastapi",
            "styling": "tailwind",
            "database": "sqlite",
        },
        "milestones": [
            {
                "id": "01-shell",
                "name": "Shell",
                "section_id": None,
                "status": "pending",
                "worktree_path": None,
                "backend_port": None,
                "frontend_port": None,
                "branch_name": None,
            },
            {
                "id": "02-dashboard",
                "name": "Dashboard",
                "section_id": "dashboard",
                "status": "pending",
                "worktree_path": None,
                "backend_port": None,
                "frontend_port": None,
                "branch_name": None,
            },
        ],
        "design_system": {
            "primary": "violet",
            "secondary": "emerald",
            "neutral": "stone",
            "fonts": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
            "tokens_css": None,
        },
        "entities": ["User", "Task"],
        "current_milestone": None,
        "model_set": "base",
        "total_cost": 0.0,
        "output_path": None,
        "created_at": None,
        "updated_at": None,
    }


@pytest.fixture
def product_plan_dir(tmp_path):
    """Create a minimal product-plan directory structure."""
    plan_dir = tmp_path / "product-plan"
    plan_dir.mkdir()

    # product-overview.md
    (plan_dir / "product-overview.md").write_text(
        "# My Test App\n\n"
        "A test application for unit testing.\n\n"
        "## Description\n\n"
        "This is a test application built for unit testing purposes.\n\n"
        "## Sections\n\n"
        "- Dashboard\n"
        "- Settings\n\n"
        "## Entities\n\n"
        "- User\n"
        "- Task\n"
    )

    # instructions/incremental/
    incremental_dir = plan_dir / "instructions" / "incremental"
    incremental_dir.mkdir(parents=True)
    (incremental_dir / "01-shell.md").write_text("# Application Shell\n\nBuild the shell.")
    (incremental_dir / "02-dashboard.md").write_text("# Dashboard\n\nBuild the dashboard.")
    (incremental_dir / "03-settings.md").write_text("# Settings\n\nBuild the settings page.")

    # design-system/
    ds_dir = plan_dir / "design-system"
    ds_dir.mkdir()
    (ds_dir / "tailwind-colors.md").write_text(
        "primary: blue\nsecondary: green\nneutral: slate\n"
    )
    (ds_dir / "fonts.md").write_text(
        "heading: Poppins\nbody: Open Sans\nmono: Fira Code\n"
    )
    (ds_dir / "tokens.css").write_text(":root { --color-primary: blue; }\n")

    # sections/
    dashboard_dir = plan_dir / "sections" / "dashboard"
    dashboard_dir.mkdir(parents=True)
    (dashboard_dir / "README.md").write_text("# Dashboard Section\n")
    (dashboard_dir / "sample-data.json").write_text('{"items": []}')
    (dashboard_dir / "types.ts").write_text("export interface DashboardItem { id: string; }")
    comp_dir = dashboard_dir / "components"
    comp_dir.mkdir()
    (comp_dir / "StatCard.tsx").write_text("export function StatCard() { return <div />; }")
    (comp_dir / "ChartWidget.tsx").write_text("export function ChartWidget() { return <div />; }")

    settings_dir = plan_dir / "sections" / "settings"
    settings_dir.mkdir(parents=True)
    (settings_dir / "README.md").write_text("# Settings Section\n")

    # shell/
    shell_dir = plan_dir / "shell"
    shell_dir.mkdir()
    (shell_dir / "README.md").write_text("# Shell\n")
    shell_comp_dir = shell_dir / "components"
    shell_comp_dir.mkdir()
    (shell_comp_dir / "Sidebar.tsx").write_text("export function Sidebar() { return <nav />; }")

    # data-shapes/
    ds_shapes = plan_dir / "data-shapes"
    ds_shapes.mkdir()
    (ds_shapes / "overview.ts").write_text(
        "export interface User { id: string; name: string; }\n"
        "export type Task = { id: string; title: string; };\n"
        "type _internal = string;\n"
    )

    return plan_dir
