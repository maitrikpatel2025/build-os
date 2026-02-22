"""Data types for Build OS pipeline."""

from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# Retry codes for Claude Code execution errors
class RetryCode(str, Enum):
    CLAUDE_CODE_ERROR = "claude_code_error"
    TIMEOUT_ERROR = "timeout_error"
    EXECUTION_ERROR = "execution_error"
    ERROR_DURING_EXECUTION = "error_during_execution"
    NONE = "none"


# Model set types
ModelSet = Literal["base", "heavy"]

# Milestone status progression
MilestoneStatus = Literal[
    "pending",
    "in_progress",
    "frontend_done",
    "backend_done",
    "wired",
    "tested",
    "complete",
]

# Tech stack options — use str so any language/framework id is allowed.
# Known built-in ids: frontend (react-vite, react-cra), backend (fastapi), styling (tailwind), database (sqlite, postgres, none).
# Custom stacks: add templates under templates/frontend/{id}/ or templates/backend/{id}/ and use that id.
FrontendFramework = str  # e.g. "react-vite", "react-cra", "next-js", "vue-vite"
BackendFramework = str   # e.g. "fastapi", "express", "go-gin"
StylingFramework = str   # e.g. "tailwind", "css-modules"
DatabaseChoice = str     # e.g. "sqlite", "postgres", "none"

# Build OS slash commands
BuildSlashCommand = Literal[
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


# --- Tech Stack ---

class TechStack(BaseModel):
    """Any language/framework: use registered ids or add templates under templates/frontend/{id}/, templates/backend/{id}/."""
    frontend: str = "react-vite"
    backend: str = "fastapi"
    styling: str = "tailwind"
    database: str = "sqlite"


# --- Design System ---

class DesignSystem(BaseModel):
    primary: str = "violet"
    secondary: str = "emerald"
    neutral: str = "stone"
    fonts: Dict[str, str] = Field(default_factory=lambda: {
        "heading": "Inter",
        "body": "Inter",
        "mono": "JetBrains Mono",
    })
    tokens_css: Optional[str] = None


# --- Build Milestone ---

class BuildMilestone(BaseModel):
    id: str                              # "01-shell", "02-dashboard"
    name: str                            # "Shell", "Dashboard"
    section_id: Optional[str] = None     # None for shell, "dashboard" for sections
    status: MilestoneStatus = "pending"
    worktree_path: Optional[str] = None
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None
    branch_name: Optional[str] = None


# --- Build State ---

class BuildStateData(BaseModel):
    build_id: str
    product_name: str
    product_plan_path: str = "product-plan/"
    tech_stack: TechStack = Field(default_factory=TechStack)
    milestones: List[BuildMilestone] = Field(default_factory=list)
    design_system: DesignSystem = Field(default_factory=DesignSystem)
    entities: List[str] = Field(default_factory=list)
    current_milestone: Optional[str] = None
    model_set: ModelSet = "base"
    total_cost: float = 0.0
    output_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --- Product Plan Parsing ---

class MilestoneInstruction(BaseModel):
    """Parsed milestone instruction from product-plan/instructions/incremental/."""
    id: str                    # "01-shell"
    name: str                  # "Shell"
    section_id: Optional[str]  # None for shell, "dashboard" for sections
    instruction_path: str      # Path to the instruction .md file
    order: int                 # Numeric order (1, 2, 3...)


class SectionComponent(BaseModel):
    """A component file within a section."""
    name: str                  # "AgentCard.tsx"
    path: str                  # Full path to the component file


class SectionAssets(BaseModel):
    """Assets for a single section from product-plan/sections/{section-id}/."""
    section_id: str
    readme_path: Optional[str] = None
    components: List[SectionComponent] = Field(default_factory=list)
    types_path: Optional[str] = None
    sample_data_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    tests_path: Optional[str] = None


class ShellAssets(BaseModel):
    """Assets for the shell from product-plan/shell/."""
    readme_path: Optional[str] = None
    components: List[SectionComponent] = Field(default_factory=list)


class ProductOverview(BaseModel):
    """Parsed product overview from product-plan/product-overview.md."""
    product_name: str
    description: Optional[str] = None
    sections: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)


class ProductPlan(BaseModel):
    """Complete parsed product plan."""
    product_overview: ProductOverview
    milestones: List[MilestoneInstruction] = Field(default_factory=list)
    design_system: DesignSystem = Field(default_factory=DesignSystem)
    sections: List[SectionAssets] = Field(default_factory=list)
    shell: ShellAssets = Field(default_factory=ShellAssets)


# --- Agent Execution ---

class AgentPromptRequest(BaseModel):
    """Claude Code agent prompt configuration."""
    prompt: str
    build_id: str
    agent_name: str = "ops"
    model: Literal["sonnet", "opus"] = "sonnet"
    dangerously_skip_permissions: bool = False
    output_file: str
    working_dir: Optional[str] = None
    disable_tools: bool = False


class AgentPromptResponse(BaseModel):
    """Claude Code agent response."""
    output: str
    success: bool
    session_id: Optional[str] = None
    retry_code: RetryCode = RetryCode.NONE


class AgentTemplateRequest(BaseModel):
    """Claude Code agent template execution request."""
    agent_name: str
    slash_command: BuildSlashCommand
    args: List[str] = Field(default_factory=list)
    build_id: str
    model: Literal["sonnet", "opus"] = "sonnet"
    working_dir: Optional[str] = None
    disable_tools: bool = False
