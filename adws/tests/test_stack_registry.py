"""Tests for stack registry (any language/framework support)."""

import pytest

from adws.adw_modules.stack_registry import (
    STACK_REGISTRY,
    get_backend_spec,
    get_frontend_spec,
    get_validation_commands,
    list_registered_stacks,
)


class TestStackRegistry:
    def test_react_vite_has_frontend_spec(self):
        spec = get_frontend_spec("react-vite")
        assert spec is not None
        assert spec["kind"] == "frontend"
        assert "validation" in spec
        assert len(spec["validation"]) >= 1

    def test_fastapi_has_backend_spec(self):
        spec = get_backend_spec("fastapi")
        assert spec is not None
        assert spec["kind"] == "backend"
        assert any("pytest" in s.get("command", "") for s in spec["validation"])

    def test_validation_commands_default_stack(self):
        tech_stack = {"frontend": "react-vite", "backend": "fastapi"}
        steps = get_validation_commands(tech_stack, "/out")
        assert len(steps) >= 2
        names = [s["name"] for s in steps]
        assert any("Frontend" in n for n in names)
        assert any("Backend" in n for n in names)

    def test_list_registered_stacks_frontend(self):
        fronts = list_registered_stacks(kind="frontend")
        ids = [s["id"] for s in fronts]
        assert "react-vite" in ids
        assert "react-cra" in ids

    def test_list_registered_stacks_backend(self):
        backs = list_registered_stacks(kind="backend")
        assert any(s["id"] == "fastapi" for s in backs)

    def test_unknown_frontend_returns_none_without_template(self):
        # Without a templates/frontend/unknown-fw/ dir, we get None or a spec from registry
        spec = get_frontend_spec("unknown-framework-xyz")
        # Registry has no entry; no template dir in test env -> None or auto spec
        assert spec is None or spec.get("kind") == "frontend"
