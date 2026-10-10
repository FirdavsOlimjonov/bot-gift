from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.database.models.base import Base
from app.database.models import Box, User
from app.handlers.admin import is_admin
from app.keyboards.boxes import boxes_keyboard
from app.services.game_service import GameService, initialize_boxes
from app.services.statistics_service import user_statistics


@pytest.fixture
async def database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(BOT_TOKEN="test", DATABASE_URL="sqlite+aiosqlite://", WINNING_BOXES="25:10000,200:5000", BOX_COUNT=200, COOLDOWN_SECONDS=300)
    async with factory() as session:
        await initialize_boxes(session, settings)
        session.add(User(telegram_id=1, first_name="Test"))
        session.add(User(telegram_id=2, first_name="Second"))
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
    clock[0] += timedelta(seconds=settings.cooldown_seconds)
    assert (await make_selection(factory, settings, clock, 2)).accepted


@pytest.mark.asyncio
async def test_winning_and_losing_boxes(database):
    factory, settings = database
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    losing = await make_selection(factory, settings, clock, 1)
    assert losing.attempt.gift_amount == 0 and not losing.attempt.is_winner
    clock[0] += timedelta(seconds=settings.cooldown_seconds)
    winning = await make_selection(factory, settings, clock, 25)
    assert winning.attempt.gift_amount == 10000 and winning.attempt.is_winner
    async with factory() as session:
        service = GameService(settings, clock=lambda: clock[0] + timedelta(seconds=settings.cooldown_seconds))
        finished = await service.select_box(session, 1, 2)
    assert finished.finished


@pytest.mark.asyncio
async def test_claimed_box_is_unavailable_to_other_users(database):
    factory, settings = database
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    service = GameService(settings, clock=lambda: clock[0])
    async with factory() as session:
        first = await service.select_box(session, 1, 25)
    assert first.accepted
    async with factory() as session:
        box = await session.scalar(__import__("sqlalchemy").select(Box).where(Box.box_number == 25))
        assert box.selected_by_name == "Test"
    async with factory() as session:
        with pytest.raises(ValueError, match="no longer available"):
            await service.select_box(session, 2, 25)


@pytest.mark.asyncio
async def test_statistics(database):
    factory, settings = database
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    await make_selection(factory, settings, clock, 1)
    clock[0] += timedelta(seconds=settings.cooldown_seconds)
    await make_selection(factory, settings, clock, 25)
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


@pytest.mark.asyncio
async def test_cooldown_is_five_minutes(database):
    factory, settings = database
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    assert (await make_selection(factory, settings, clock, 1)).accepted
    clock[0] += timedelta(minutes=4, seconds=59)
    assert not (await make_selection(factory, settings, clock, 2)).accepted
    clock[0] += timedelta(seconds=1)
    assert (await make_selection(factory, settings, clock, 2)).accepted


@pytest.mark.asyncio
async def test_two_hundred_boxes(database):
    factory, settings = database
    async with factory() as session:
        boxes = (await session.scalars(__import__("sqlalchemy").select(Box))).all()
    assert len(boxes) == 200
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    result = await make_selection(factory, settings, clock, 200)
    assert result.attempt.is_winner and result.attempt.gift_amount == 5000
    async with factory() as session:
        with pytest.raises(ValueError):
            await GameService(settings).select_box(session, 2, 201)


def test_boxes_keyboard_pages_stay_under_telegram_limit():
    available = list(range(1, 201))
    for page in range(4):
        markup = boxes_keyboard(available, [None] * 200, page=page, box_count=200)
        buttons = [button for row in markup.inline_keyboard for button in row]
        assert len(buttons) <= 100
        numbered = [b.callback_data for b in buttons if b.callback_data.startswith("box:")]
        assert numbered[0] == f"box:{page * 50 + 1}" and numbered[-1] == f"box:{page * 50 + 50}"


@pytest.mark.asyncio
async def test_winner_is_blocked_and_detected(database):
    from app.services.game_service import winning_amount, won_text

    factory, settings = database
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    async with factory() as session:
        assert await winning_amount(session, 1) is None
    await make_selection(factory, settings, clock, 25)
    async with factory() as session:
        assert await winning_amount(session, 1) == 10000
        assert await winning_amount(session, 2) is None
    clock[0] += timedelta(hours=1)  # even long after the cooldown
    result = await make_selection(factory, settings, clock, 3)
    assert result.finished and not result.accepted
    assert "allaqachon yutgansiz" in won_text(10000)
