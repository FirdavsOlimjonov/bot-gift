from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.database.models.base import Base
from app.database.models import Box, User
from app.handlers.admin import is_admin
from app.services.game_service import GameService, initialize_boxes
from app.services.statistics_service import user_statistics


@pytest.fixture
async def database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(BOT_TOKEN="test", DATABASE_URL="sqlite+aiosqlite://", WINNING_BOXES="25:10000")
    async with factory() as session:
        await initialize_boxes(session, settings)
        session.add(User(telegram_id=1, first_name="Test"))
        await session.commit()
    yield factory, settings
    await engine.dispose()


async def make_selection(factory, settings, clock, box):
    service = GameService(settings, clock=lambda: clock[0])
    async with factory() as session:
        return await service.select_box(session, 1, box)


@pytest.mark.asyncio
async def test_cooldown_and_expiration(database):
    factory, settings = database
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    first = await make_selection(factory, settings, clock, 1)
    assert first.accepted
    blocked = await make_selection(factory, settings, clock, 2)
    assert not blocked.accepted
    clock[0] += timedelta(minutes=2)
    assert (await make_selection(factory, settings, clock, 2)).accepted


@pytest.mark.asyncio
async def test_winning_and_losing_boxes(database):
    factory, settings = database
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    losing = await make_selection(factory, settings, clock, 1)
    assert losing.attempt.gift_amount == 0 and not losing.attempt.is_winner
    clock[0] += timedelta(minutes=2)
    winning = await make_selection(factory, settings, clock, 25)
    assert winning.attempt.gift_amount == 10000 and winning.attempt.is_winner


@pytest.mark.asyncio
async def test_statistics(database):
    factory, settings = database
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    await make_selection(factory, settings, clock, 25)
    clock[0] += timedelta(minutes=2)
    await make_selection(factory, settings, clock, 1)
    async with factory() as session:
        user = await session.get(User, 1)
        data = await user_statistics(session, user.id)
    assert data["attempts"] == 2
    assert data["winners"] == 1
    assert data["money"] == 10000


def test_admin_authorization():
    class Actor:
        def __init__(self, user_id):
            self.from_user = type("TelegramUser", (), {"id": user_id})()

    assert is_admin(Actor(123), {123})
    assert not is_admin(Actor(456), {123})
