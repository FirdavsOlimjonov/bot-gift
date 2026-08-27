from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database.models import Box, GameAttempt, User


@dataclass(frozen=True)
class SelectionResult:
    accepted: bool
    attempt: GameAttempt | None = None
    next_allowed_at: datetime | None = None


class GameService:
    def __init__(self, settings: Settings, clock=None) -> None:
        self.settings = settings
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    async def select_box(self, session: AsyncSession, telegram_id: int, box_number: int) -> SelectionResult:
        if not 1 <= box_number <= 100:
            raise ValueError("Box number must be between 1 and 100")

        async with session.begin():
            if session.bind and session.bind.dialect.name == "sqlite":
                await session.execute(text("BEGIN IMMEDIATE"))
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id).with_for_update()
            )
            if user is None or user.is_blocked:
                raise PermissionError("User is missing or blocked")

            now = self.clock()
            last_attempt = await session.scalar(
                select(GameAttempt)
                .where(GameAttempt.user_id == user.id)
                .order_by(desc(GameAttempt.created_at))
                .limit(1)
            )
            if last_attempt and last_attempt.created_at and last_attempt.created_at.tzinfo is None:
                last_attempt.created_at = last_attempt.created_at.replace(tzinfo=timezone.utc)
            if last_attempt and last_attempt.created_at + timedelta(seconds=self.settings.cooldown_seconds) > now:
                next_allowed = last_attempt.created_at + timedelta(seconds=self.settings.cooldown_seconds)
                return SelectionResult(False, next_allowed_at=next_allowed)

            box = await session.scalar(
                select(Box).where(Box.box_number == box_number).with_for_update()
            )
            if box is None:
                raise LookupError("Box configuration is missing")
            if not box.is_available:
                raise ValueError("Box is no longer available")
            box.is_available = False
            box.selected_by_name = user.first_name or user.username or "Noma'lum"
            attempt = GameAttempt(
                user_id=user.id,
                box_number=box.box_number,
                gift_amount=box.gift_amount,
                is_winner=box.is_winner,
                created_at=now,
            )
            session.add(attempt)
            await session.flush()
            return SelectionResult(True, attempt=attempt)


async def initialize_boxes(session: AsyncSession, settings: Settings) -> None:
    configured = settings.configured_winning_boxes
    async with session.begin():
        existing = {box.box_number: box for box in (await session.scalars(select(Box))).all()}
        for number in range(1, 101):
            amount = configured.get(number, 0)
            box = existing.get(number)
            if box is None:
                session.add(Box(box_number=number, gift_amount=amount, is_winner=amount > 0))
            elif number in configured:
                box.gift_amount = amount
                box.is_winner = amount > 0


async def ensure_user(session: AsyncSession, telegram_user) -> User:
    async with session.begin():
        user = await session.scalar(select(User).where(User.telegram_id == telegram_user.id).with_for_update())
        if user is None:
            user = User(telegram_id=telegram_user.id)
            session.add(user)
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        await session.flush()
        return user
