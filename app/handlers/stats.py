from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from app.database.models import User
from app.services.statistics_service import user_statistics
from app.utils import as_utc, format_money, format_time, remaining_text

router = Router()


async def send_stats(message: Message, session_factory, game_service) -> None:
    async with session_factory() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        data = await user_statistics(session, user.id) if user else {"attempts": 0, "winners": 0, "money": 0, "last_attempt": None}
    next_allowed = None
    if data["last_attempt"]:
        from datetime import timedelta
        next_allowed = as_utc(data["last_attempt"]) + timedelta(seconds=game_service.settings.cooldown_seconds)
    next_text = "Hozir" if not next_allowed or next_allowed <= game_service.clock() else remaining_text(next_allowed)
    await message.answer(f"🏆 SIZNING STATISTIKANGIZ\n\n🎯 Jami urinishlar: {data['attempts']}\n🎁 Tanlangan qutilar: {data['attempts']}\n💰 Yutuqlar soni: {data['winners']}\n💵 Jami yutuq: {format_money(data['money'])}\n\n⏳ Keyingi urinish:\n{next_text}")


@router.message(Command("stats"))
@router.message(F.text == "🏆 Mening yutuqlarim")
async def stats(message: Message, session_factory, game_service) -> None:
    await send_stats(message, session_factory, game_service)
