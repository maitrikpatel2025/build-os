"""Build state management for Build OS.

Provides persistent state management for the build pipeline,
tracking milestone progression, worktree mappings, and cost accumulation.
"""

import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from .data_types import BuildStateData, BuildMilestone, MilestoneStatus
from .utils import get_project_root


class BuildState:
    """Container for Build OS workflow state with file persistence."""

    STATE_FILENAME = "build_state.json"

    def __init__(self, build_id: str):
        if not build_id:
            raise ValueError("build_id is required for BuildState")

        self.build_id = build_id
        self.data: Dict[str, Any] = {"build_id": self.build_id}
        self.logger = logging.getLogger(__name__)

    def update(self, **kwargs) -> None:
        """Update state with new key-value pairs."""
        for key, value in kwargs.items():
            self.data[key] = value
        self.data["updated_at"] = datetime.now().isoformat()

    def get(self, key: str, default=None):
        """Get value from state by key."""
        return self.data.get(key, default)

    def get_milestones(self) -> List[Dict[str, Any]]:
        """Get all milestones from state."""
        return self.data.get("milestones", [])

    def get_milestone(self, milestone_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific milestone by ID."""
        for m in self.get_milestones():
            if m["id"] == milestone_id:
                return m
        return None

    def update_milestone(self, milestone_id: str, **kwargs) -> bool:
        """Update a specific milestone's fields.

        Args:
            milestone_id: The milestone ID to update
            **kwargs: Fields to update (status, worktree_path, etc.)

        Returns:
            True if milestone was found and updated, False otherwise
        """
        milestones = self.get_milestones()
        for i, m in enumerate(milestones):
            if m["id"] == milestone_id:
                milestones[i].update(kwargs)
                self.data["milestones"] = milestones
                self.data["updated_at"] = datetime.now().isoformat()
                return True
        return False

    def get_current_milestone(self) -> Optional[Dict[str, Any]]:
        """Get the current active milestone."""
        current_id = self.data.get("current_milestone")
        if current_id:
            return self.get_milestone(current_id)
        return None

    def set_current_milestone(self, milestone_id: Optional[str]) -> None:
        """Set the current active milestone."""
        self.data["current_milestone"] = milestone_id
        self.data["updated_at"] = datetime.now().isoformat()

    def get_next_pending_milestone(self) -> Optional[Dict[str, Any]]:
        """Get the next milestone that is not complete."""
        for m in self.get_milestones():
            if m["status"] != "complete":
                return m
        return None

    def add_cost(self, amount: float) -> None:
        """Add to the total cost tracker."""
        current = self.data.get("total_cost", 0.0)
        self.data["total_cost"] = current + amount

    def get_output_path(self) -> Optional[str]:
        """Get the output project path."""
        return self.data.get("output_path")

    def get_state_dir(self) -> str:
        """Get the directory for this build's state files."""
        project_root = get_project_root()
        return os.path.join(project_root, "agents", self.build_id)

    def get_state_path(self) -> str:
        """Get path to state file."""
        return os.path.join(self.get_state_dir(), self.STATE_FILENAME)

    def save(self, workflow_step: Optional[str] = None) -> None:
        """Save state to file in agents/{build_id}/build_state.json."""
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)

        # Validate with Pydantic before saving
        state_data = BuildStateData(**self.data)

        with open(state_path, "w") as f:
            json.dump(state_data.model_dump(), f, indent=2)

        self.logger.info(f"Saved state to {state_path}")
        if workflow_step:
            self.logger.info(f"State updated by: {workflow_step}")

    @classmethod
    def load(cls, build_id: str, logger: Optional[logging.Logger] = None) -> Optional["BuildState"]:
        """Load state from file if it exists."""
        project_root = get_project_root()
        state_path = os.path.join(project_root, "agents", build_id, cls.STATE_FILENAME)

        if not os.path.exists(state_path):
            return None

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            # Validate with Pydantic
            state_data = BuildStateData(**data)

            state = cls(state_data.build_id)
            state.data = state_data.model_dump()

            if logger:
                logger.info(f"Loaded build state from {state_path}")

            return state
        except Exception as e:
            if logger:
                logger.error(f"Failed to load state from {state_path}: {e}")
            return None

    @classmethod
    def find_latest(cls, logger: Optional[logging.Logger] = None) -> Optional["BuildState"]:
        """Find the most recently updated build state."""
        project_root = get_project_root()
        agents_dir = os.path.join(project_root, "agents")

        if not os.path.exists(agents_dir):
            return None

        latest_state = None
        latest_time = None

        for entry in os.listdir(agents_dir):
            state_path = os.path.join(agents_dir, entry, cls.STATE_FILENAME)
            if os.path.exists(state_path):
                try:
                    mtime = os.path.getmtime(state_path)
                    if latest_time is None or mtime > latest_time:
                        latest_time = mtime
                        latest_state = cls.load(entry, logger)
                except Exception:
                    continue

        return latest_state

    @classmethod
    def from_stdin(cls) -> Optional["BuildState"]:
        """Read state from stdin if available (for piped input)."""
        if sys.stdin.isatty():
            return None
        try:
            input_data = sys.stdin.read()
            if not input_data.strip():
                return None
            data = json.loads(input_data)
            build_id = data.get("build_id")
            if not build_id:
                return None
            state = cls(build_id)
            state.data = data
            return state
        except (json.JSONDecodeError, EOFError):
            return None

    def to_stdout(self) -> None:
        """Write state to stdout as JSON (for piping to next script)."""
        print(json.dumps(self.data, indent=2))
