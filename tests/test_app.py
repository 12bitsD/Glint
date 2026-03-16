from glint.app import GlintApp
from glint.turn_parser import Turn
from glint.widgets.turn_widget import TurnWidget


async def test_app_starts_without_crashing():
    app = GlintApp(command=["echo", "hi"])
    async with app.run_test(headless=True) as pilot:
        await pilot.pause(0.2)
        assert app.is_running


async def test_app_add_turn_renders_widget():
    app = GlintApp(command=["echo", "hi"])
    async with app.run_test(headless=True) as pilot:
        turn = Turn(id=1, prompt_text="test prompt")
        turn.response_bytes.extend(b"test output\n")
        turn.is_complete = True
        app.add_turn(turn)
        await pilot.pause(0.1)
        assert len(app.query(TurnWidget)) >= 1


async def test_app_j_k_navigation():
    app = GlintApp(command=["echo", "hi"])
    async with app.run_test(headless=True) as pilot:
        for i in range(2):
            t = Turn(id=i, prompt_text=f"prompt {i}")
            t.response_bytes.extend(f"output {i}\n".encode())
            t.is_complete = True
            app.add_turn(t)
        await pilot.pause(0.1)
        await pilot.press("j")
        assert app.focused_turn_id is not None
