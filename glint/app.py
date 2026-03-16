from __future__ import annotations

import os
import signal

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Header, Input

from glint.pty_manager import PTYManager
from glint.turn_parser import Turn, TurnParser
from glint.widgets.turn_widget import TurnWidget


class GlintApp(App):
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("j", "focus_next_turn", "Next", show=True),
        Binding("k", "focus_prev_turn", "Prev", show=True),
        Binding("enter", "toggle_turn", "Expand", show=True),
        Binding("g", "focus_first_turn", "Top", show=False),
        Binding("G", "focus_last_turn", "Bottom", show=False),
        Binding("`", "toggle_raw", "Raw", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, command: list[str]) -> None:
        super().__init__()
        self.command = command
        self._parser = TurnParser()
        self._pty: PTYManager | None = None
        self.focused_turn_id: int | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ScrollableContainer(id="turn-list")
        yield Input(placeholder="> ", id="prompt-input")
        yield Footer()

    def on_mount(self) -> None:
        try:
            rows, cols = os.get_terminal_size()
        except OSError:
            rows, cols = 24, 80

        self._pty = PTYManager(
            command=self.command,
            on_output=self._on_pty_output,
            dimensions=(rows, cols),
        )
        try:
            self._pty.start()
        except (FileNotFoundError, OSError) as e:
            self.exit(message=f"glint: command not found: {self.command[0]}\n{e}")
            return

        signal.signal(signal.SIGWINCH, self._on_sigwinch)
        self.query_one("#prompt-input", Input).focus()

    def _on_sigwinch(self, signum: int, frame: object) -> None:
        try:
            rows, cols = os.get_terminal_size()
        except OSError:
            return
        self._resize_pty(rows, cols)

    def _resize_pty(self, rows: int, cols: int) -> None:
        if self._pty:
            self._pty.resize(rows, cols)

    def _on_pty_output(self, data: bytes) -> None:
        self.call_from_thread(self._handle_output, data)

    def _handle_output(self, data: bytes) -> None:
        self._parser.feed_output(data)
        if self._parser.current_turn:
            turn_list = self.query_one("#turn-list", ScrollableContainer)
            existing = {w.turn.id: w for w in turn_list.query(TurnWidget)}
            t = self._parser.current_turn
            if t.id in existing:
                existing[t.id].append_output(data)
            else:
                widget = TurnWidget(turn=t)
                turn_list.mount(widget)
                if self.focused_turn_id is None:
                    self.focused_turn_id = t.id

    def add_turn(self, turn: Turn) -> None:
        self._parser.turns.append(turn)
        self._parser.current_turn = turn
        turn_list = self.query_one("#turn-list", ScrollableContainer)
        widget = TurnWidget(turn=turn)
        turn_list.mount(widget)
        if self.focused_turn_id is None:
            self.focused_turn_id = turn.id

    def on_input_submitted(self, event: Input.Submitted) -> None:
        prompt_text = event.value.strip()
        if not prompt_text:
            return
        event.input.clear()
        self._parser.feed_prompt(prompt_text)
        if self._pty:
            self._pty.write((prompt_text + "\n").encode())

    def _get_turn_widgets(self) -> list[TurnWidget]:
        return list(self.query_one("#turn-list", ScrollableContainer).query(TurnWidget))

    def action_focus_next_turn(self) -> None:
        widgets = self._get_turn_widgets()
        if not widgets:
            return
        ids = [w.turn.id for w in widgets]
        if self.focused_turn_id is None or self.focused_turn_id not in ids:
            self.focused_turn_id = ids[0]
        else:
            idx = ids.index(self.focused_turn_id)
            self.focused_turn_id = ids[min(idx + 1, len(ids) - 1)]
        self._highlight_focused()

    def action_focus_prev_turn(self) -> None:
        widgets = self._get_turn_widgets()
        if not widgets:
            return
        ids = [w.turn.id for w in widgets]
        if self.focused_turn_id is None or self.focused_turn_id not in ids:
            self.focused_turn_id = ids[-1]
        else:
            idx = ids.index(self.focused_turn_id)
            self.focused_turn_id = ids[max(idx - 1, 0)]
        self._highlight_focused()

    def action_focus_first_turn(self) -> None:
        widgets = self._get_turn_widgets()
        if widgets:
            self.focused_turn_id = widgets[0].turn.id
            self._highlight_focused()

    def action_focus_last_turn(self) -> None:
        widgets = self._get_turn_widgets()
        if widgets:
            self.focused_turn_id = widgets[-1].turn.id
            self._highlight_focused()

    def action_toggle_turn(self) -> None:
        for w in self._get_turn_widgets():
            if w.turn.id == self.focused_turn_id:
                w.toggle()
                break

    def action_toggle_raw(self) -> None:
        self.notify("Raw view not yet implemented")

    def _highlight_focused(self) -> None:
        for w in self._get_turn_widgets():
            if w.turn.id == self.focused_turn_id:
                w.add_class("focused")
                w.scroll_visible()
            else:
                w.remove_class("focused")

    def on_unmount(self) -> None:
        if self._pty:
            self._pty.terminate()
