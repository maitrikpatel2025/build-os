"""Tests for adws.adw_modules.agent_sdk — Agent SDK wrapper types and hooks."""

from adws.adw_modules.agent_sdk import (
    HookEvent,
    HooksConfig,
    MessageHandlers,
    ModelName,
    QueryInput,
    QueryOutput,
    create_log_hooks,
    create_message_handlers,
)


class TestModelName:
    def test_sonnet_value(self):
        assert ModelName.SONNET == "claude-sonnet-4-5-20250929"

    def test_opus_value(self):
        assert ModelName.OPUS == "claude-opus-4-6"

    def test_haiku_value(self):
        assert ModelName.HAIKU == "claude-haiku-4-5-20251001"


class TestQueryInput:
    def test_defaults(self):
        qi = QueryInput(prompt="Hello")
        assert qi.model == ModelName.SONNET
        assert qi.max_turns == 25
        assert qi.system_prompt is None
        assert qi.working_dir is None
        assert not qi.dangerously_skip_permissions

    def test_custom(self):
        qi = QueryInput(
            prompt="Build the app",
            model=ModelName.OPUS,
            system_prompt="You are a builder",
            max_turns=10,
            working_dir="/tmp/work",
        )
        assert qi.model == ModelName.OPUS
        assert qi.max_turns == 10


class TestQueryOutput:
    def test_success_defaults(self):
        qo = QueryOutput(result="done")
        assert qo.success is True
        assert qo.cost_usd == 0.0
        assert qo.num_turns == 0
        assert qo.error is None

    def test_failure(self):
        qo = QueryOutput(result="", success=False, error="API error")
        assert not qo.success
        assert qo.error == "API error"

    def test_with_cost(self):
        qo = QueryOutput(result="done", cost_usd=0.0523, num_turns=3)
        assert qo.cost_usd == 0.0523
        assert qo.num_turns == 3


class TestHookEvent:
    def test_empty(self):
        event = HookEvent()
        assert event.tool_name is None
        assert event.build_id is None

    def test_with_data(self):
        event = HookEvent(
            tool_name="Write",
            tool_input={"path": "/tmp/test.py"},
            build_id="abc123",
            milestone_id="01-shell",
        )
        assert event.tool_name == "Write"
        assert event.build_id == "abc123"


class TestHooksConfig:
    def test_empty_hooks(self):
        hooks = HooksConfig()
        assert hooks.pre_tool_use == []
        assert hooks.post_tool_use == []
        assert hooks.stop == []

    def test_with_hooks(self):
        called = []

        def on_pre(event):
            called.append("pre")

        def on_post(event):
            called.append("post")

        hooks = HooksConfig(pre_tool_use=[on_pre], post_tool_use=[on_post])
        event = HookEvent(tool_name="test")

        for hook in hooks.pre_tool_use:
            hook(event)
        for hook in hooks.post_tool_use:
            hook(event)

        assert called == ["pre", "post"]


class TestMessageHandlers:
    def test_empty(self):
        mh = MessageHandlers()
        assert mh.on_assistant_block is None
        assert mh.on_result is None

    def test_with_handlers(self):
        blocks = []
        results = []

        mh = MessageHandlers(
            on_assistant_block=lambda text: blocks.append(text),
            on_result=lambda output: results.append(output),
        )

        mh.on_assistant_block("hello")
        mh.on_result(QueryOutput(result="done"))

        assert blocks == ["hello"]
        assert len(results) == 1
        assert results[0].result == "done"


class TestCreateLogHooks:
    def test_creates_hooks_config(self, logger):
        hooks = create_log_hooks("build001", "01-shell", logger)
        assert isinstance(hooks, HooksConfig)
        assert len(hooks.pre_tool_use) == 1
        assert len(hooks.post_tool_use) == 1
        assert len(hooks.stop) == 1

    def test_hooks_callable(self, logger):
        hooks = create_log_hooks("build001", "01-shell", logger)
        event = HookEvent(tool_name="Write", step_name="complete")

        # Should not raise
        for hook in hooks.pre_tool_use:
            hook(event)
        for hook in hooks.post_tool_use:
            hook(event)
        for hook in hooks.stop:
            hook(event)


class TestCreateMessageHandlers:
    def test_creates_handlers(self, logger):
        handlers = create_message_handlers("build001", logger)
        assert isinstance(handlers, MessageHandlers)
        assert handlers.on_assistant_block is not None
        assert handlers.on_result is not None

    def test_handlers_callable(self, logger):
        handlers = create_message_handlers("build001", logger)

        # Should not raise
        handlers.on_assistant_block("test text")
        handlers.on_result(QueryOutput(result="done", cost_usd=0.01))
