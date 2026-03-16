from __future__ import annotations

import re
from dataclasses import dataclass, field

# Matches ANSI escape sequences (complex pattern — not obvious without comment)
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[mGKHF]|\x1b\][^\x07]*\x07|\x1b[^[]")


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


@dataclass
class Turn:
    id: int
    prompt_text: str
    response_bytes: bytearray = field(default_factory=bytearray)
    is_complete: bool = False

    def summary(self, max_len: int = 60) -> str:
        text = self.response_bytes.decode("utf-8", errors="replace")
        for line in text.splitlines():
            stripped = _strip_ansi(line).strip()
            if stripped:
                return stripped[:max_len]
        return "(no output)"


class TurnParser:
    """Not thread-safe — call from one thread only."""

    def __init__(self) -> None:
        self.turns: list[Turn] = []
        self.current_turn: Turn | None = None
        self._next_id: int = 0

    def feed_output(self, data: bytes) -> None:
        if self.current_turn is None:
            self._open_turn(prompt_text="")
        assert self.current_turn is not None
        self.current_turn.response_bytes.extend(data)

    def feed_prompt(self, prompt_text: str) -> None:
        if self.current_turn is not None:
            self.complete_current_turn()
        self._open_turn(prompt_text=prompt_text)

    def complete_current_turn(self) -> None:
        if self.current_turn is not None:
            self.current_turn.is_complete = True

    def _open_turn(self, prompt_text: str) -> None:
        turn = Turn(id=self._next_id, prompt_text=prompt_text)
        self._next_id += 1
        self.turns.append(turn)
        self.current_turn = turn
