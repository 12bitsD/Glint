from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static

from glint.turn_parser import Turn


class TurnWidget(Widget):
    is_expanded: reactive[bool] = reactive(False, init=False)

    def __init__(self, turn: Turn) -> None:
        super().__init__()
        self.turn = turn

    def compose(self) -> ComposeResult:
        yield Label(self._collapsed_label(expanded=False), id="collapsed-label")
        yield Static("", id="expanded-content")

    def on_mount(self) -> None:
        self._refresh_display()

    def watch_is_expanded(self, value: bool) -> None:
        if self.is_attached:
            self._refresh_display()

    def _collapsed_label(self, expanded: bool) -> str:
        prompt = self.turn.prompt_text[:60] if self.turn.prompt_text else self.turn.summary()
        indicator = "↓" if expanded else "›"
        return f"{indicator}  {prompt}"

    def _refresh_display(self) -> None:
        collapsed = self.query_one("#collapsed-label", Label)
        expanded = self.query_one("#expanded-content", Static)

        if self.is_expanded:
            collapsed.update(self._collapsed_label(expanded=True))
            collapsed.display = True
            raw = self.turn.response_bytes.decode("utf-8", errors="replace")
            expanded.update(Text.from_ansi(raw))
            expanded.display = True
        else:
            collapsed.update(self._collapsed_label(expanded=False))
            collapsed.display = True
            expanded.display = False

    def collapsed_text(self) -> str:
        return self._collapsed_label(expanded=self.is_expanded)

    def toggle(self) -> None:
        self.is_expanded = not self.is_expanded

    def append_output(self, data: bytes) -> None:
        self.turn.response_bytes.extend(data)
        if self.is_expanded:
            raw = self.turn.response_bytes.decode("utf-8", errors="replace")
            self.query_one("#expanded-content", Static).update(Text.from_ansi(raw))
