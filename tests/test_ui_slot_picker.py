"""Test for SlotPickerScreen UI component."""

import pytest

from src.core.game_loop import GameSession
from src.ui.app import ChronicleApp, SlotPickerScreen


@pytest.mark.asyncio
async def test_slot_picker_screen_instantiation() -> None:
    """Verify SlotPickerScreen instantiates without arguments and composes using app.session.save_dir."""
    app = ChronicleApp(session=GameSession())
    async with app.run_test() as pilot:
        await app.push_screen(SlotPickerScreen())
        await pilot.pause()
        assert isinstance(app.screen, SlotPickerScreen)
        title = app.screen.query_one("#slot-title")
        assert title is not None
