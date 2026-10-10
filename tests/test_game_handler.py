"""Handler-level tests for box selection, using fake aiogram objects."""
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.database.models import Box, User
from app.database.models.base import Base
from app.handlers.game import choose_box
from app.services.game_service import GameService, initialize_boxes


class FakeMessage:
    def __init__(self):
        self.answers = []
        self.markups = []

    async def answer(self, text, reply_markup=None, **kwargs):
        self.answers.append(text)

    async def edit_reply_markup(self, reply_markup=None):
        self.markups.append(reply_markup)


class FakeCallback:
    def __init__(self, data, user_id=42, first_name="Ali"):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id, username=None, first_name=first_name, last_name=None)
        self.message = FakeMessage()

    async def answer(self, *args, **kwargs):
        pass


@pytest.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(BOT_TOKEN="test", WINNING_BOXES="7:500", BOX_COUNT=200, COOLDOWN_SECONDS=300)
    async with factory() as session:
        await initialize_boxes(session, settings)
    yield factory, settings, GameService(settings)
    await engine.dispose()


async def test_box_click_works_without_start(env):
    """After a restart the users table is empty; clicking a box must still work."""
    factory, settings, service = env
    callback = FakeCallback("box:12")
    await choose_box(callback, factory, settings, service)
    assert "12-qutini" in callback.message.answers[-1]
    async with factory() as session:
        assert await session.scalar(select(User).where(User.telegram_id == 42)) is not None
        box = await session.scalar(select(Box).where(Box.box_number == 12))
        assert not box.is_available and box.selected_by_name == "Ali"


async def test_winner_then_blocked(env):
    factory, settings, service = env
    first = FakeCallback("box:7")
    await choose_box(first, factory, settings, service)
    assert "TABRIKLAYMIZ" in first.message.answers[-1]
    second = FakeCallback("box:8")
    await choose_box(second, factory, settings, service)
    assert "allaqachon yutgansiz" in second.message.answers[-1]


async def test_taken_box_message(env):
    factory, settings, service = env
    await choose_box(FakeCallback("box:150", user_id=1), factory, settings, service)
    other = FakeCallback("box:150", user_id=2)
    await choose_box(other, factory, settings, service)
    assert "allaqachon tanlangan" in other.message.answers[-1]
