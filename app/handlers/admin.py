from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import desc, func, select

from app.database.models import Box, GameAttempt, User
from app.keyboards.admin import admin_keyboard
from app.services.statistics_service import admin_statistics
from app.utils import format_money

router = Router()


def is_admin(message_or_callback, admin_ids: set[int]) -> bool:
    return message_or_callback.from_user.id in admin_ids


@router.message(Command("admin"))
async def admin(message: Message, settings) -> None:
    if not is_admin(message, settings.admin_id_set):
        await message.answer("⛔ Kirish taqiqlangan.")
        return
    await message.answer("🔐 ADMIN PANEL", reply_markup=admin_keyboard())


@router.message(Command("box"))
async def set_box(message: Message, settings, session_factory) -> None:
    if not is_admin(message, settings.admin_id_set):
        await message.answer("⛔ Kirish taqiqlangan.")
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Format: /box <raqam> <summa>")
        return
    try:
        number, amount = int(parts[1]), int(parts[2])
        if not 1 <= number <= 100 or amount < 0:
            raise ValueError
    except ValueError:
        await message.answer("Quti 1-100 oralig'ida, summa esa musbat bo'lishi kerak.")
        return
    async with session_factory() as session:
        async with session.begin():
            box = await session.scalar(select(Box).where(Box.box_number == number).with_for_update())
            if not box:
                await message.answer("Quti topilmadi.")
                return
            box.gift_amount, box.is_winner = amount, amount > 0
    await message.answer(f"✅ Box #{number}: {format_money(amount)}")


@router.message(Command("remove_box"))
async def remove_box(message: Message, settings, session_factory) -> None:
    if not is_admin(message, settings.admin_id_set):
        await message.answer("⛔ Kirish taqiqlangan.")
        return
    try:
        number = int(message.text.split()[1])
    except (ValueError, IndexError):
        await message.answer("Format: /remove_box <raqam>")
        return
    async with session_factory() as session:
        async with session.begin():
            box = await session.scalar(select(Box).where(Box.box_number == number).with_for_update())
            if box:
                box.gift_amount, box.is_winner = 0, False
    await message.answer(f"✅ Box #{number} sovg'asi olib tashlandi.")


@router.callback_query(F.data == "admin:stats")
async def stats(callback: CallbackQuery, settings, session_factory) -> None:
    if not is_admin(callback, settings.admin_id_set): return await callback.answer("⛔")
    async with session_factory() as session:
        data = await admin_statistics(session)
    total, winners, money = data["total"]
    today_total, today_winners, today_money = data["today"]
    await callback.message.answer(f"📊 GAME STATISTICS\n\n👥 Total users: {data['users']}\n🎯 Total attempts: {total}\n🏆 Winners: {winners}\n💰 Total money awarded: {format_money(money)}\n\n📅 Today:\nAttempts: {today_total}\nWinners: {today_winners}\nMoney: {format_money(today_money)}")
    await callback.answer()


@router.callback_query(F.data == "admin:users")
async def users(callback: CallbackQuery, settings, session_factory) -> None:
    if not is_admin(callback, settings.admin_id_set): return await callback.answer("⛔")
    async with session_factory() as session:
        total = await session.scalar(select(func.count(User.id)))
        active = await session.scalar(select(func.count(User.id)).where(User.is_blocked.is_(False)))
    await callback.message.answer(f"👥 USERS\n\nTotal users: {total}\nActive users: {active}")
    await callback.answer()


@router.callback_query(F.data == "admin:boxes")
async def boxes(callback: CallbackQuery, settings, session_factory) -> None:
    if not is_admin(callback, settings.admin_id_set): return await callback.answer("⛔")
    async with session_factory() as session:
        rows = (await session.scalars(select(Box).where(Box.is_winner.is_(True)).order_by(Box.box_number))).all()
    text = "📦 BOX CONFIGURATION\n\n" + ("\n".join(f"Box #{box.box_number} → {format_money(box.gift_amount)}" for box in rows) or "Winning boxes are not configured.")
    navigation = []
    if page > 0:
        navigation.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"admin:winners:{page - 1}"))
    if len(rows) == 10:
        navigation.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"admin:winners:{page + 1}"))
    markup = InlineKeyboardMarkup(inline_keyboard=[navigation]) if navigation else None
    await callback.message.answer(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:report:"))
async def report(callback: CallbackQuery, settings, session_factory) -> None:
    if not is_admin(callback, settings.admin_id_set): return await callback.answer("⛔")
    period = callback.data.rsplit(":", 1)[1]
    now = datetime.now(timezone.utc)
    since = {"today": now.replace(hour=0, minute=0, second=0, microsecond=0), "yesterday": now - timedelta(days=1), "7d": now - timedelta(days=7), "30d": now - timedelta(days=30), "all": datetime.min.replace(tzinfo=timezone.utc)}.get(period, datetime.min.replace(tzinfo=timezone.utc))
    async with session_factory() as session:
        new_users = await session.scalar(select(func.count(User.id)).where(User.created_at >= since))
        attempts, winners, money = (await session.execute(select(func.count(GameAttempt.id), func.count(GameAttempt.id).filter(GameAttempt.is_winner.is_(True)), func.coalesce(func.sum(GameAttempt.gift_amount), 0)).where(GameAttempt.created_at >= since))).one()
    await callback.message.answer(f"📊 REPORT\n\nPeriod: {period}\n\n👥 New users: {new_users}\n🎯 Attempts: {attempts}\n🏆 Winners: {winners}\n💰 Money awarded: {format_money(money)}")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:winners:"))
async def winners(callback: CallbackQuery, settings, session_factory) -> None:
    if not is_admin(callback, settings.admin_id_set): return await callback.answer("⛔")
    page = max(0, int(callback.data.rsplit(":", 1)[1]))
    async with session_factory() as session:
        rows = (await session.execute(select(GameAttempt, User).join(User).where(GameAttempt.is_winner.is_(True)).order_by(desc(GameAttempt.created_at)).offset(page * 10).limit(10))).all()
    text = "🏆 WINNERS\n\n" + ("\n\n".join(f"👤 @{user.username or '-'}\n🆔 Telegram ID: {user.telegram_id}\n📦 Box: #{attempt.box_number}\n💰 Gift: {format_money(attempt.gift_amount)}\n🕐 {attempt.created_at.astimezone().strftime('%d.%m.%Y %H:%M')}" for attempt, user in rows) or "No winners.")
    await callback.message.answer(text)
    await callback.answer()
