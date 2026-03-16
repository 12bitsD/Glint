from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static

from glint.turn_parser import Turn


class TurnWidget(Widget):
    is_expanded: reactive[bool] = reactive(False)

    def __init__(self, turn: Turn) -> None:
        super().__init__()
        self.turn = turn

    def compose(self) -> ComposeResult:
        summary = self.turn.summary()
        prefix = f"▶ Turn {self.turn.id}"
        if self.turn.prompt_text:
            prefix += f" — {self.turn.prompt_text[:40]}"
        yield Label(f"{prefix}  {summary}", id="collapsed-label")
        yield Static("", id="expanded-content")

    def on_mount(self) -> None:
        self._refresh_display()

    def watch_is_expanded(self, value: bool) -> None:
        self._refresh_display()

    def _refresh_display(self) -> None:
        collapsed = self.query_one("#collapsed-label", Label)
        expanded = self.query_one("#expanded-content", Static)

        if self.is_expanded:
            collapsed.display = False
            raw = self.turn.response_bytes.decode("utf-8", errors="replace")
            expanded.update(Text.from_ansi(raw))
            expanded.display = True
        else:
            summary = self.turn.summary()
            prefix = "▶"
            collapsed.update(
                f"{prefix} Turn {self.turn.id}"
                + (f" — {self.turn.prompt_text[:40]}" if self.turn.prompt_text else "")
                + f"  {summary}"
            )
            collapsed.display = True
            expanded.display = False

    def collapsed_text(self) -> str:
        return self.query_one("#collapsed-label", Label).content

    def toggle(self) -> None:
        self.is_expanded = not self.is_expanded

    def append_output(self, data: bytes) -> None:
        self.turn.response_bytes.extend(data)
        if self.is_expanded:
            raw = self.turn.response_bytes.decode("utf-8", errors="replace")
            self.query_one("#expanded-content", Static).update(Text.from_ansi(raw))
