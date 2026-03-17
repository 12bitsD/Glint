import pytest
from textual.app import App, ComposeResult

from glint.turn_parser import Turn
from glint.widgets.turn_widget import TurnWidget


class _TestApp(App):
    def __init__(self, widget: TurnWidget):
        super().__init__()
        self._widget = widget

    def compose(self) -> ComposeResult:
        yield self._widget


async def test_turn_widget_collapsed_shows_prompt():
    turn = Turn(id=1, prompt_text="fix the bug")
    turn.response_bytes.extend(b"I'll fix the bug in auth.py\n")
    widget = TurnWidget(turn=turn)

    async with _TestApp(widget).run_test() as pilot:
        assert widget.is_expanded is False
        assert "fix the bug" in widget.collapsed_text()


async def test_turn_widget_collapsed_falls_back_to_summary_when_no_prompt():
    turn = Turn(id=1, prompt_text="")
    turn.response_bytes.extend(b"startup output line\n")
    widget = TurnWidget(turn=turn)

    async with _TestApp(widget).run_test() as pilot:
        assert "startup output line" in widget.collapsed_text()


async def test_turn_widget_toggle_expands():
    turn = Turn(id=2, prompt_text="hello")
    turn.response_bytes.extend(b"response text\n")
    widget = TurnWidget(turn=turn)

    async with _TestApp(widget).run_test() as pilot:
        assert widget.is_expanded is False
        widget.toggle()
        assert widget.is_expanded is True


async def test_turn_widget_expanded_shows_full_content():
    turn = Turn(id=3, prompt_text="go")
    turn.response_bytes.extend(b"line one\nline two\nline three\n")
    widget = TurnWidget(turn=turn)

    async with _TestApp(widget).run_test() as pilot:
        widget.toggle()
        expanded = widget.query_one("#expanded-content")
        assert expanded.display is True


async def test_turn_widget_append_output_updates_expanded_view():
    turn = Turn(id=4, prompt_text="stream")
    turn.response_bytes.extend(b"initial line\n")
    widget = TurnWidget(turn=turn)

    async with _TestApp(widget).run_test() as pilot:
        widget.toggle()
        assert widget.is_expanded is True

        widget.append_output(b"new line\n")
        await pilot.pause(0.1)

        assert b"initial line" in widget.turn.response_bytes
        assert b"new line" in widget.turn.response_bytes
        assert widget.is_expanded is True
