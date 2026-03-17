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


from glint.turn_parser import TurnParser


def test_parser_initial_state():
    p = TurnParser()
    assert p.turns == []
    assert p.current_turn is None


def test_parser_startup_output_before_prompt():
    p = TurnParser()
    p.feed_output(b"Welcome to claude\n")
    assert len(p.turns) == 1
    assert p.turns[0].id == 0
    assert p.turns[0].prompt_text == ""
    assert b"Welcome to claude" in p.turns[0].response_bytes


def test_parser_prompt_opens_new_turn():
    p = TurnParser()
    p.feed_output(b"startup\n")
    p.feed_prompt("fix the bug")
    assert len(p.turns) == 2
    assert p.current_turn.id == 1
    assert p.current_turn.prompt_text == "fix the bug"


def test_parser_output_goes_to_current_turn():
    p = TurnParser()
    p.feed_prompt("hello")
    p.feed_output(b"AI response here\n")
    assert b"AI response here" in p.current_turn.response_bytes


def test_parser_complete_marks_turn():
    p = TurnParser()
    p.feed_prompt("go")
    p.feed_output(b"done\n")
    p.complete_current_turn()
    assert p.turns[-1].is_complete is True


def test_parser_multiple_turns():
    p = TurnParser()
    p.feed_prompt("turn 1")
    p.feed_output(b"response 1\n")
    p.feed_prompt("turn 2")
    p.feed_output(b"response 2\n")
    assert len(p.turns) == 2
    assert b"response 1" in p.turns[0].response_bytes
    assert b"response 2" in p.turns[1].response_bytes


def test_parser_previous_turn_completed_on_new_prompt():
    p = TurnParser()
    p.feed_output(b"startup\n")
    assert p.turns[0].is_complete is False
    p.feed_prompt("hello")
    assert p.turns[0].is_complete is True


def test_parser_consecutive_prompts_no_output():
    p = TurnParser()
    p.feed_prompt("prompt 1")
    p.feed_prompt("prompt 2")
    assert len(p.turns) == 2
    assert p.turns[0].is_complete is True
    assert p.turns[0].response_bytes == bytearray()
    assert p.turns[1].prompt_text == "prompt 2"
    assert p.turns[1].response_bytes == bytearray()


def test_turn_summary_all_ansi_returns_no_output():
    t = Turn(id=6, prompt_text="")
    t.response_bytes.extend(b"\x1b[1m\x1b[0m\n\x1b[32m\x1b[0m\n")
    assert t.summary() == "(no output)"
