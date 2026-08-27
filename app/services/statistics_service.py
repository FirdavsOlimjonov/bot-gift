from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import GameAttempt, User


async def user_statistics(session: AsyncSession, user_id: int) -> dict:
    row = await session.execute(
        select(
            func.count(GameAttempt.id),
            func.count(GameAttempt.id).filter(GameAttempt.is_winner.is_(True)),
            func.coalesce(func.sum(GameAttempt.gift_amount), 0),
            func.max(GameAttempt.created_at),
        ).where(GameAttempt.user_id == user_id)
    )
    total, winners, money, last_attempt = row.one()
    return {"attempts": total, "winners": winners, "money": money, "last_attempt": last_attempt}


async def admin_statistics(session: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    totals = await session.execute(select(func.count(User.id)).select_from(User))
    active = await session.execute(select(func.count(User.id)).where(User.is_blocked.is_(False)))
    aggregate = await session.execute(select(func.count(GameAttempt.id), func.count(GameAttempt.id).filter(GameAttempt.is_winner.is_(True)), func.coalesce(func.sum(GameAttempt.gift_amount), 0)))
    daily = await session.execute(select(func.count(GameAttempt.id), func.count(GameAttempt.id).filter(GameAttempt.is_winner.is_(True)), func.coalesce(func.sum(GameAttempt.gift_amount), 0)).where(GameAttempt.created_at >= today))
    return {"users": totals.scalar_one(), "active_users": active.scalar_one(), "total": aggregate.one(), "today": daily.one()}
