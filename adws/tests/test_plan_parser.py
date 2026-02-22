"""Tests for adws.adw_modules.plan_parser — Product plan parsing."""

import pytest

from adws.adw_modules.plan_parser import (
    parse_design_system,
    parse_entities_from_data_shapes,
    parse_milestones,
    parse_product_overview,
    parse_product_plan,
    parse_sections,
    parse_shell,
)


class TestParseProductOverview:
    def test_parses_product_name(self, product_plan_dir):
        overview = parse_product_overview(str(product_plan_dir))
        assert overview.product_name == "My Test App"

    def test_parses_description(self, product_plan_dir):
        overview = parse_product_overview(str(product_plan_dir))
        # Description is extracted from first paragraph after the H1 title
        assert overview.description is not None

    def test_parses_sections(self, product_plan_dir):
        overview = parse_product_overview(str(product_plan_dir))
        assert "Dashboard" in overview.sections
        assert "Settings" in overview.sections

    def test_parses_entities(self, product_plan_dir):
        overview = parse_product_overview(str(product_plan_dir))
        assert "User" in overview.entities
        assert "Task" in overview.entities

    def test_missing_overview_file(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        overview = parse_product_overview(str(empty_dir))
        assert overview.product_name == "Unknown Product"


class TestParseMilestones:
    def test_parses_all_milestones(self, product_plan_dir):
        milestones = parse_milestones(str(product_plan_dir))
        assert len(milestones) == 3

    def test_milestone_ids(self, product_plan_dir):
        milestones = parse_milestones(str(product_plan_dir))
        ids = [m.id for m in milestones]
        assert "01-shell" in ids
        assert "02-dashboard" in ids
        assert "03-settings" in ids

    def test_milestone_ordering(self, product_plan_dir):
        milestones = parse_milestones(str(product_plan_dir))
        orders = [m.order for m in milestones]
        assert orders == sorted(orders)

    def test_shell_has_no_section_id(self, product_plan_dir):
        milestones = parse_milestones(str(product_plan_dir))
        shell = [m for m in milestones if m.id == "01-shell"][0]
        assert shell.section_id is None

    def test_sections_have_section_id(self, product_plan_dir):
        milestones = parse_milestones(str(product_plan_dir))
        dashboard = [m for m in milestones if m.id == "02-dashboard"][0]
        assert dashboard.section_id == "dashboard"

    def test_names_extracted_from_h1(self, product_plan_dir):
        milestones = parse_milestones(str(product_plan_dir))
        shell = [m for m in milestones if m.id == "01-shell"][0]
        assert shell.name == "Application Shell"

    def test_missing_directory(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        milestones = parse_milestones(str(empty_dir))
        assert milestones == []

    def test_ignores_non_md_files(self, product_plan_dir):
        incremental = product_plan_dir / "instructions" / "incremental"
        (incremental / "notes.txt").write_text("not a milestone")
        milestones = parse_milestones(str(product_plan_dir))
        assert len(milestones) == 3  # unchanged


class TestParseDesignSystem:
    def test_parses_colors(self, product_plan_dir):
        ds = parse_design_system(str(product_plan_dir))
        assert ds.primary == "blue"
        assert ds.secondary == "green"
        assert ds.neutral == "slate"

    def test_parses_fonts(self, product_plan_dir):
        ds = parse_design_system(str(product_plan_dir))
        assert ds.fonts["heading"] == "Poppins"
        assert ds.fonts["body"] == "Open Sans"
        assert ds.fonts["mono"] == "Fira Code"

    def test_parses_tokens_css(self, product_plan_dir):
        ds = parse_design_system(str(product_plan_dir))
        assert ds.tokens_css is not None
        assert "--color-primary" in ds.tokens_css

    def test_missing_directory_returns_defaults(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        ds = parse_design_system(str(empty_dir))
        assert ds.primary == "violet"  # default
        assert ds.secondary == "emerald"  # default


class TestParseSections:
    def test_finds_all_sections(self, product_plan_dir):
        sections = parse_sections(str(product_plan_dir))
        ids = [s.section_id for s in sections]
        assert "dashboard" in ids
        assert "settings" in ids

    def test_dashboard_assets(self, product_plan_dir):
        sections = parse_sections(str(product_plan_dir))
        dashboard = [s for s in sections if s.section_id == "dashboard"][0]
        assert dashboard.readme_path is not None
        assert dashboard.sample_data_path is not None
        assert dashboard.types_path is not None

    def test_dashboard_components(self, product_plan_dir):
        sections = parse_sections(str(product_plan_dir))
        dashboard = [s for s in sections if s.section_id == "dashboard"][0]
        comp_names = [c.name for c in dashboard.components]
        assert "StatCard.tsx" in comp_names
        assert "ChartWidget.tsx" in comp_names

    def test_settings_minimal(self, product_plan_dir):
        sections = parse_sections(str(product_plan_dir))
        settings = [s for s in sections if s.section_id == "settings"][0]
        assert settings.readme_path is not None
        assert settings.components == []

    def test_missing_directory(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        sections = parse_sections(str(empty_dir))
        assert sections == []


class TestParseShell:
    def test_shell_readme(self, product_plan_dir):
        shell = parse_shell(str(product_plan_dir))
        assert shell.readme_path is not None

    def test_shell_components(self, product_plan_dir):
        shell = parse_shell(str(product_plan_dir))
        comp_names = [c.name for c in shell.components]
        assert "Sidebar.tsx" in comp_names

    def test_missing_directory(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        shell = parse_shell(str(empty_dir))
        assert shell.readme_path is None
        assert shell.components == []


class TestParseEntitiesFromDataShapes:
    def test_extracts_interfaces_and_types(self, product_plan_dir):
        entities = parse_entities_from_data_shapes(str(product_plan_dir))
        assert "User" in entities
        assert "Task" in entities

    def test_filters_internal_types(self, product_plan_dir):
        entities = parse_entities_from_data_shapes(str(product_plan_dir))
        assert "_internal" not in entities

    def test_missing_file(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        entities = parse_entities_from_data_shapes(str(empty_dir))
        assert entities == []


class TestParseProductPlan:
    def test_full_parse(self, product_plan_dir):
        plan = parse_product_plan(str(product_plan_dir))
        assert plan.product_overview.product_name == "My Test App"
        assert len(plan.milestones) == 3
        assert plan.design_system.primary == "blue"
        assert len(plan.sections) == 2
        assert plan.shell.readme_path is not None

    def test_missing_plan_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_product_plan(str(tmp_path / "nonexistent"))
