"""Tests for adws.adw_modules.data_types — Pydantic models and enums."""

import pytest
from pydantic import ValidationError

from adws.adw_modules.data_types import (
    AgentPromptRequest,
    AgentPromptResponse,
    AgentTemplateRequest,
    BuildMilestone,
    BuildStateData,
    DesignSystem,
    MilestoneInstruction,
    ProductOverview,
    ProductPlan,
    RetryCode,
    SectionAssets,
    SectionComponent,
    TechStack,
)

# --- Enum tests ---

class TestRetryCode:
    def test_values(self):
        assert RetryCode.CLAUDE_CODE_ERROR == "claude_code_error"
        assert RetryCode.TIMEOUT_ERROR == "timeout_error"
        assert RetryCode.EXECUTION_ERROR == "execution_error"
        assert RetryCode.ERROR_DURING_EXECUTION == "error_during_execution"
        assert RetryCode.NONE == "none"

    def test_string_comparison(self):
        assert RetryCode.NONE == "none"
        assert RetryCode("claude_code_error") == RetryCode.CLAUDE_CODE_ERROR


# --- TechStack ---

class TestTechStack:
    def test_defaults(self):
        ts = TechStack()
        assert ts.frontend == "react-vite"
        assert ts.backend == "fastapi"
        assert ts.styling == "tailwind"
        assert ts.database == "sqlite"

    def test_custom_values(self):
        ts = TechStack(frontend="react-cra", database="postgres")
        assert ts.frontend == "react-cra"
        assert ts.database == "postgres"

    def test_any_frontend_accepted(self):
        ts = TechStack(frontend="next-js")
        assert ts.frontend == "next-js"

    def test_any_database_accepted(self):
        ts = TechStack(database="mongodb")
        assert ts.database == "mongodb"


# --- DesignSystem ---

class TestDesignSystem:
    def test_defaults(self):
        ds = DesignSystem()
        assert ds.primary == "violet"
        assert ds.secondary == "emerald"
        assert ds.neutral == "stone"
        assert ds.fonts["heading"] == "Inter"
        assert ds.fonts["body"] == "Inter"
        assert ds.fonts["mono"] == "JetBrains Mono"
        assert ds.tokens_css is None

    def test_custom_colors(self):
        ds = DesignSystem(primary="blue", secondary="green", neutral="slate")
        assert ds.primary == "blue"

    def test_custom_fonts(self):
        fonts = {"heading": "Poppins", "body": "Roboto", "mono": "Fira Code"}
        ds = DesignSystem(fonts=fonts)
        assert ds.fonts["heading"] == "Poppins"


# --- BuildMilestone ---

class TestBuildMilestone:
    def test_minimal(self):
        m = BuildMilestone(id="01-shell", name="Shell")
        assert m.status == "pending"
        assert m.section_id is None
        assert m.worktree_path is None

    def test_full(self):
        m = BuildMilestone(
            id="02-dashboard",
            name="Dashboard",
            section_id="dashboard",
            status="in_progress",
            backend_port=9300,
            frontend_port=9400,
            branch_name="build-abc-02-dashboard",
        )
        assert m.section_id == "dashboard"
        assert m.backend_port == 9300

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            BuildMilestone(id="01-shell", name="Shell", status="invalid")

    def test_all_valid_statuses(self):
        for status in ["pending", "in_progress", "frontend_done", "backend_done", "wired", "tested", "complete"]:
            m = BuildMilestone(id="01-shell", name="Shell", status=status)
            assert m.status == status


# --- BuildStateData ---

class TestBuildStateData:
    def test_minimal(self):
        bsd = BuildStateData(build_id="abc12345", product_name="My App")
        assert bsd.build_id == "abc12345"
        assert bsd.product_name == "My App"
        assert bsd.milestones == []
        assert bsd.total_cost == 0.0
        assert bsd.model_set == "base"

    def test_full(self, sample_build_state_data):
        bsd = BuildStateData(**sample_build_state_data)
        assert bsd.build_id == sample_build_state_data["build_id"]
        assert len(bsd.milestones) == 2
        assert bsd.milestones[0].id == "01-shell"
        assert bsd.tech_stack.frontend == "react-vite"
        assert bsd.design_system.primary == "violet"
        assert bsd.entities == ["User", "Task"]

    def test_model_dump_round_trip(self, sample_build_state_data):
        bsd = BuildStateData(**sample_build_state_data)
        dumped = bsd.model_dump()
        bsd2 = BuildStateData(**dumped)
        assert bsd2.build_id == bsd.build_id
        assert len(bsd2.milestones) == len(bsd.milestones)

    def test_missing_build_id_rejected(self):
        with pytest.raises(ValidationError):
            BuildStateData(product_name="My App")

    def test_missing_product_name_rejected(self):
        with pytest.raises(ValidationError):
            BuildStateData(build_id="abc12345")


# --- Product Plan types ---

class TestMilestoneInstruction:
    def test_creation(self):
        mi = MilestoneInstruction(
            id="01-shell",
            name="Shell",
            section_id=None,
            instruction_path="/path/to/01-shell.md",
            order=1,
        )
        assert mi.id == "01-shell"
        assert mi.section_id is None
        assert mi.order == 1


class TestSectionAssets:
    def test_defaults(self):
        sa = SectionAssets(section_id="dashboard")
        assert sa.components == []
        assert sa.readme_path is None
        assert sa.sample_data_path is None

    def test_with_components(self):
        sa = SectionAssets(
            section_id="dashboard",
            components=[SectionComponent(name="Card.tsx", path="/path/Card.tsx")],
        )
        assert len(sa.components) == 1
        assert sa.components[0].name == "Card.tsx"


class TestProductOverview:
    def test_minimal(self):
        po = ProductOverview(product_name="Test")
        assert po.product_name == "Test"
        assert po.sections == []
        assert po.entities == []


class TestProductPlan:
    def test_defaults(self):
        pp = ProductPlan(
            product_overview=ProductOverview(product_name="Test")
        )
        assert pp.milestones == []
        assert pp.sections == []


# --- Agent types ---

class TestAgentPromptRequest:
    def test_creation(self):
        req = AgentPromptRequest(
            prompt="Build the shell",
            build_id="abc12345",
            output_file="/tmp/output.jsonl",
        )
        assert req.model == "sonnet"
        assert req.agent_name == "ops"
        assert not req.dangerously_skip_permissions

    def test_opus_model(self):
        req = AgentPromptRequest(
            prompt="Build the shell",
            build_id="abc12345",
            model="opus",
            output_file="/tmp/output.jsonl",
        )
        assert req.model == "opus"


class TestAgentPromptResponse:
    def test_success(self):
        resp = AgentPromptResponse(output="Done!", success=True)
        assert resp.retry_code == RetryCode.NONE

    def test_failure(self):
        resp = AgentPromptResponse(
            output="Error", success=False, retry_code=RetryCode.TIMEOUT_ERROR
        )
        assert not resp.success
        assert resp.retry_code == RetryCode.TIMEOUT_ERROR


class TestAgentTemplateRequest:
    def test_creation(self):
        req = AgentTemplateRequest(
            agent_name="ops",
            slash_command="/build-os/init",
            build_id="abc12345",
        )
        assert req.args == []
        assert req.model == "sonnet"

    def test_e2e_slash_command_accepted(self):
        req = AgentTemplateRequest(
            agent_name="e2e_test_runner",
            slash_command="/build-os/test-e2e-section",
            build_id="abc12345",
            args=["abc12345", "dashboard"],
        )
        assert req.slash_command == "/build-os/test-e2e-section"
