from glint.turn_parser import Turn


def test_turn_defaults():
    t = Turn(id=1, prompt_text="hello")
    assert t.id == 1
    assert t.prompt_text == "hello"
    assert t.response_bytes == bytearray()
    assert t.is_complete is False


def test_turn_append():
    t = Turn(id=1, prompt_text="")
    t.response_bytes.extend(b"some output\n")
    assert b"some output" in t.response_bytes


def test_turn_summary_plain_text():
    t = Turn(id=2, prompt_text="fix the bug")
    t.response_bytes.extend(b"I'll fix the auth bug now\nmore lines\n")
    assert t.summary() == "I'll fix the auth bug now"


def test_turn_summary_strips_ansi():
    t = Turn(id=3, prompt_text="")
    t.response_bytes.extend(b"\x1b[1m\x1b[32mHello world\x1b[0m\nmore\n")
    assert t.summary() == "Hello world"


def test_turn_summary_skips_blank_lines():
    t = Turn(id=4, prompt_text="")
    t.response_bytes.extend(b"\n\n  \nFirst real line\n")
    assert t.summary() == "First real line"


def test_turn_summary_truncates():
    t = Turn(id=5, prompt_text="")
    t.response_bytes.extend(("x" * 100 + "\n").encode())
    assert len(t.summary()) == 60
