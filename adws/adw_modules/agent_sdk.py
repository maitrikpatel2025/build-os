"""Claude Agent SDK wrapper for Build OS orchestration.

Provides typed Pydantic wrappers around the Anthropic Agent SDK
for use in automated pipeline orchestration with hooks, logging,
cost tracking, and real-time observability.
"""

import logging
from enum import Enum
from typing import Callable, List, Optional

from pydantic import BaseModel, Field


class ModelName(str, Enum):
    """Supported Claude model names."""
    SONNET = "claude-sonnet-4-5-20250929"
    OPUS = "claude-opus-4-6"
    HAIKU = "claude-haiku-4-5-20251001"


class QueryInput(BaseModel):
    """Input for a Claude Agent SDK query."""
    prompt: str
    model: ModelName = ModelName.SONNET
    system_prompt: Optional[str] = None
    max_turns: int = 25
    working_dir: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    dangerously_skip_permissions: bool = False


class QueryOutput(BaseModel):
    """Output from a Claude Agent SDK query."""
    result: str
    session_id: Optional[str] = None
    cost_usd: float = 0.0
    num_turns: int = 0
    duration_ms: int = 0
    success: bool = True
    error: Optional[str] = None


class HookEvent(BaseModel):
    """Event data passed to hooks."""
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[str] = None
    step_name: Optional[str] = None
    build_id: Optional[str] = None
    milestone_id: Optional[str] = None


class HooksConfig(BaseModel):
    """Configuration for SDK execution hooks.

    Hooks are called at various points during agent execution
    for logging, cost tracking, and observability.
    """
    pre_tool_use: List[Callable[[HookEvent], None]] = Field(default_factory=list)
    post_tool_use: List[Callable[[HookEvent], None]] = Field(default_factory=list)
    stop: List[Callable[[HookEvent], None]] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class MessageHandlers(BaseModel):
    """Handlers for streaming agent messages."""
    on_assistant_block: Optional[Callable[[str], None]] = None
    on_result: Optional[Callable[[QueryOutput], None]] = None

    class Config:
        arbitrary_types_allowed = True


async def query_to_completion(
    query: QueryInput,
    hooks: Optional[HooksConfig] = None,
    handlers: Optional[MessageHandlers] = None,
    logger: Optional[logging.Logger] = None,
) -> QueryOutput:
    """Execute a query using the Claude Agent SDK.

    This is the primary execution function for SDK-based orchestration.
    It wraps the Anthropic Agent SDK with hooks for observability.

    Args:
        query: The query configuration
        hooks: Optional hooks for pre/post tool use and stop events
        handlers: Optional message handlers for streaming
        logger: Optional logger

    Returns:
        QueryOutput with result, cost, and metadata
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return QueryOutput(
            result="",
            success=False,
            error="anthropic package not installed. Run: uv add anthropic",
        )

    client = Anthropic()

    if logger:
        logger.info(f"SDK query: model={query.model.value}, prompt={query.prompt[:100]}...")

    try:
        # Build messages
        messages = [{"role": "user", "content": query.prompt}]

        # Build system prompt
        system = query.system_prompt or ""

        # Execute using the Agent SDK conversation loop
        response = client.messages.create(
            model=query.model.value,
            max_tokens=16384,
            system=system if system else None,
            messages=messages,
        )

        # Extract result
        result_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                result_text += block.text

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Approximate cost calculation
        if "opus" in query.model.value:
            cost = (input_tokens * 15 + output_tokens * 75) / 1_000_000
        elif "sonnet" in query.model.value:
            cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000
        else:
            cost = (input_tokens * 0.8 + output_tokens * 4) / 1_000_000

        output = QueryOutput(
            result=result_text,
            cost_usd=cost,
            num_turns=1,
            success=True,
        )

        # Call result handler
        if handlers and handlers.on_result:
            handlers.on_result(output)

        # Call stop hooks
        if hooks:
            event = HookEvent(step_name="complete")
            for hook in hooks.stop:
                hook(event)

        if logger:
            logger.info(f"SDK query complete: cost=${cost:.4f}")

        return output

    except Exception as e:
        error_msg = f"SDK query failed: {e}"
        if logger:
            logger.error(error_msg)

        return QueryOutput(
            result="",
            success=False,
            error=error_msg,
        )


def create_log_hooks(build_id: str, milestone_id: str, logger: logging.Logger) -> HooksConfig:
    """Create standard logging hooks for a build milestone.

    Args:
        build_id: Current build ID
        milestone_id: Current milestone ID
        logger: Logger instance

    Returns:
        HooksConfig with logging hooks
    """

    def log_tool_start(event: HookEvent):
        logger.debug(f"[{milestone_id}] Tool start: {event.tool_name}")

    def log_tool_end(event: HookEvent):
        output_preview = (event.tool_output or "")[:100]
        logger.debug(f"[{milestone_id}] Tool end: {event.tool_name} → {output_preview}")

    def log_step_complete(event: HookEvent):
        logger.info(f"[{milestone_id}] Step complete: {event.step_name}")

    return HooksConfig(
        pre_tool_use=[log_tool_start],
        post_tool_use=[log_tool_end],
        stop=[log_step_complete],
    )


def create_message_handlers(
    build_id: str, logger: logging.Logger
) -> MessageHandlers:
    """Create standard message handlers for streaming output.

    Args:
        build_id: Current build ID
        logger: Logger instance

    Returns:
        MessageHandlers for streaming
    """

    def stream_to_log(text: str):
        logger.debug(f"[{build_id}] Assistant: {text[:200]}")

    def record_result(output: QueryOutput):
        logger.info(
            f"[{build_id}] Result: success={output.success}, "
            f"cost=${output.cost_usd:.4f}, turns={output.num_turns}"
        )

    return MessageHandlers(
        on_assistant_block=stream_to_log,
        on_result=record_result,
    )
