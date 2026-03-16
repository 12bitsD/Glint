from __future__ import annotations

import threading
from collections.abc import Callable

import ptyprocess


class PTYManager:
    def __init__(
        self,
        command: list[str],
        on_output: Callable[[bytes], None],
        dimensions: tuple[int, int] = (24, 80),
    ) -> None:
        self.command = command
        self.on_output = on_output
        self.dimensions = dimensions
        self._process: ptyprocess.PtyProcess | None = None
        self._thread: threading.Thread | None = None
        self._done = threading.Event()
        self.exit_code: int | None = None

    def start(self) -> None:
        rows, cols = self.dimensions
        self._process = ptyprocess.PtyProcess.spawn(
            self.command,
            dimensions=(rows, cols),
        )
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self) -> None:
        assert self._process is not None
        try:
            while True:
                try:
                    data = self._process.read(4096)
                except EOFError:
                    break
                if data:
                    self.on_output(data)
        finally:
            self.exit_code = self._process.wait()
            self._done.set()

    def write(self, data: bytes) -> None:
        if self._process and self._process.isalive():
            self._process.write(data)

    def resize(self, rows: int, cols: int) -> None:
        if self._process and self._process.isalive():
            self._process.setwinsize(rows, cols)

    def wait(self, timeout: float | None = None) -> None:
        self._done.wait(timeout=timeout)

    def terminate(self) -> None:
        if self._process and self._process.isalive():
            self._process.terminate(force=True)
