from glint.pty_manager import PTYManager


def test_pty_manager_runs_command():
    output_chunks: list[bytes] = []

    def on_output(data: bytes) -> None:
        output_chunks.append(data)

    mgr = PTYManager(command=["echo", "hello from pty"], on_output=on_output)
    mgr.start()
    mgr.wait(timeout=3.0)

    all_output = b"".join(output_chunks)
    assert b"hello from pty" in all_output


def test_pty_manager_exit_code():
    mgr = PTYManager(command=["sh", "-c", "exit 42"], on_output=lambda _: None)
    mgr.start()
    mgr.wait(timeout=3.0)
    assert mgr.exit_code == 42


def test_pty_manager_not_found():
    import pytest
    with pytest.raises((FileNotFoundError, OSError)):
        mgr = PTYManager(command=["__nonexistent_cmd__"], on_output=lambda _: None)
        mgr.start()
        mgr.wait(timeout=1.0)
