"""Stack registry for Build OS: any language, any framework.

Maps stack ids (e.g. react-vite, fastapi, next-js, express) to template paths,
validation commands, and dev commands. Built-in entries for known stacks;
custom stacks use templates under templates/frontend/{id}/ and
templates/backend/{id}/ and can be registered via STACK_REGISTRY or a config file.
"""

import os
from typing import Any, Dict, List, Optional

from .utils import get_project_root


# Validation command: run from output project root; cwd is relative to that.
ValidationStep = Dict[str, str]  # {"name": "...", "cwd": "app/server", "command": "uv run pytest -v"}


def _root() -> str:
    return get_project_root()


# Built-in stack specs. Keys: frontend | backend | styling | database.
# template_path: relative to project root; if set and path exists, scaffold copies from there.
# validation: list of steps for validate/finalize.
# start_dev: command to run for dev server (used by scripts/start.sh convention).
STACK_REGISTRY: Dict[str, Dict[str, Any]] = {
    # --- Frontend ---
    "react-vite": {
        "kind": "frontend",
        "label": "React (Vite)",
        "template_path": None,  # uses built-in generator in scaffold_ops
        "validation": [
            {"name": "Frontend build", "cwd": "app/client", "command": "npm run build"},
            {"name": "Frontend lint", "cwd": "app/client", "command": "npx eslint src/ --no-error-on-unmatched-pattern"},
        ],
        "start_dev": "npm run dev",
        "file_extensions": [".jsx", ".js", ".tsx", ".ts"],
    },
    "react-cra": {
        "kind": "frontend",
        "label": "React (Create React App)",
        "template_path": None,
        "validation": [
            {"name": "Frontend build", "cwd": "app/client", "command": "npm run build"},
            {"name": "Frontend lint", "cwd": "app/client", "command": "npx eslint src/ --no-error-on-unmatched-pattern"},
        ],
        "start_dev": "npm run dev",
        "file_extensions": [".jsx", ".js", ".tsx", ".ts"],
    },
    # --- Backend ---
    "fastapi": {
        "kind": "backend",
        "label": "FastAPI (Python)",
        "template_path": None,
        "validation": [
            {"name": "Backend tests", "cwd": "app/server", "command": "uv run pytest -v"},
            {"name": "Backend lint", "cwd": "app/server", "command": "uv run ruff check ."},
        ],
        "start_dev": "uv run uvicorn server:app --host 0.0.0.0 --port ${BACKEND_PORT:-8000} --reload",
        "file_extensions": [".py"],
    },
    # --- Styling (optional; most stacks use tailwind) ---
    "tailwind": {
        "kind": "styling",
        "label": "Tailwind CSS",
        "template_path": None,
        "validation": [],
        "file_extensions": [],
    },
    # --- Database ---
    "sqlite": {
        "kind": "database",
        "label": "SQLite",
        "template_path": None,
        "validation": [],
        "file_extensions": [],
    },
    "postgres": {
        "kind": "database",
        "label": "PostgreSQL",
        "template_path": None,
        "validation": [],
        "file_extensions": [],
    },
    "none": {
        "kind": "database",
        "label": "None",
        "template_path": None,
        "validation": [],
        "file_extensions": [],
    },
}


def get_frontend_spec(stack_id: str) -> Optional[Dict[str, Any]]:
    """Return frontend spec for stack_id. Checks registry then templates/frontend/{id}/."""
    spec = STACK_REGISTRY.get(stack_id)
    if spec and spec.get("kind") == "frontend":
        return spec
    template_dir = os.path.join(_root(), "templates", "frontend", stack_id)
    if os.path.isdir(template_dir):
        return {
            "kind": "frontend",
            "label": stack_id,
            "template_path": f"templates/frontend/{stack_id}",
            "validation": [
                {"name": "Frontend build", "cwd": "app/client", "command": "npm run build"},
                {"name": "Frontend lint", "cwd": "app/client", "command": "npx eslint src/ --no-error-on-unmatched-pattern"},
            ],
            "start_dev": "npm run dev",
            "file_extensions": [".jsx", ".js", ".tsx", ".ts", ".vue", ".svelte"],
        }
    return spec if spec else None


def get_backend_spec(stack_id: str) -> Optional[Dict[str, Any]]:
    """Return backend spec for stack_id. Checks registry then templates/backend/{id}/."""
    spec = STACK_REGISTRY.get(stack_id)
    if spec and spec.get("kind") == "backend":
        return spec
    template_dir = os.path.join(_root(), "templates", "backend", stack_id)
    if os.path.isdir(template_dir):
        return {
            "kind": "backend",
            "label": stack_id,
            "template_path": f"templates/backend/{stack_id}",
            "validation": [
                {"name": "Backend tests", "cwd": "app/server", "command": "npm test 2>/dev/null || true"},
                {"name": "Backend lint", "cwd": "app/server", "command": "npm run lint 2>/dev/null || true"},
            ],
            "start_dev": "npm run dev",
            "file_extensions": [".js", ".ts", ".py", ".go"],
        }
    return spec if spec else None


def get_styling_spec(stack_id: str) -> Optional[Dict[str, Any]]:
    """Return styling spec for stack_id."""
    spec = STACK_REGISTRY.get(stack_id)
    if spec and spec.get("kind") == "styling":
        return spec
    return None


def get_database_spec(stack_id: str) -> Optional[Dict[str, Any]]:
    """Return database spec for stack_id."""
    return STACK_REGISTRY.get(stack_id) if STACK_REGISTRY.get(stack_id, {}).get("kind") == "database" else None


def get_validation_commands(tech_stack: Dict[str, str], output_path: str) -> List[ValidationStep]:
    """Return ordered validation steps for the given tech_stack.

    tech_stack: dict with keys frontend, backend (and optionally styling, database).
    output_path: absolute path to the output project (so steps can be run from there).

    Returns list of {"name", "cwd", "command"} where cwd is relative to output_path.
    """
    steps: List[ValidationStep] = []
    seen: set = set()

    for kind, getter in [("frontend", get_frontend_spec), ("backend", get_backend_spec)]:
        stack_id = (tech_stack or {}).get(kind)
        if not stack_id or stack_id in seen:
            continue
        seen.add(stack_id)
        spec = getter(stack_id) if kind == "frontend" else get_backend_spec(stack_id)
        if spec and spec.get("validation"):
            for step in spec["validation"]:
                steps.append({**step})

    return steps


def get_validation_commands_for_build(build_id: str) -> List[ValidationStep]:
    """Load build state for build_id and return validation steps for its tech_stack.
    Use this from validate/finalize to run stack-appropriate commands.
    """
    from .build_state import BuildState
    state = BuildState.load(build_id)
    if not state or not state.data:
        return []
    tech_stack = state.data.get("tech_stack") or {}
    if not isinstance(tech_stack, dict):
        tech_stack = {"frontend": getattr(tech_stack, "frontend", "react-vite"), "backend": getattr(tech_stack, "backend", "fastapi")}
    output_path = state.data.get("output_path") or ""
    return get_validation_commands(tech_stack, output_path)


def list_registered_stacks(kind: Optional[str] = None) -> List[Dict[str, str]]:
    """List registered stack ids and labels. kind = frontend | backend | styling | database."""
    result = []
    for sid, spec in STACK_REGISTRY.items():
        if kind and spec.get("kind") != kind:
            continue
        result.append({"id": sid, "label": spec.get("label", sid), "kind": spec.get("kind", "")})
    return result


def has_template_for(stack_id: str, kind: str) -> bool:
    """True if we have a template dir for this stack (registry template_path or templates/{kind}/{id}/)."""
    spec = STACK_REGISTRY.get(stack_id)
    if spec:
        tp = spec.get("template_path")
        if tp:
            return os.path.isdir(os.path.join(_root(), tp))
        if spec.get("kind") == kind:
            return True  # built-in generator
    path = os.path.join(_root(), "templates", kind, stack_id)
    return os.path.isdir(path)
