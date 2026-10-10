from datetime import timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy import desc, select

from app.database.models import Box, GameAttempt, User
from app.keyboards.boxes import boxes_keyboard, page_count
from app.services.game_service import GameService
from app.utils import as_utc, format_money, format_time, remaining_text

router = Router()


async def build_boxes_keyboard(session_factory, settings, page: int = 0):
    async with session_factory() as session:
        boxes = (await session.scalars(select(Box).order_by(Box.box_number))).all()
    available = [box.box_number for box in boxes if box.is_available]
    claimed_names = [None] * settings.box_count
    for box in boxes:
        if 1 <= box.box_number <= settings.box_count:
            claimed_names[box.box_number - 1] = box.selected_by_name
    return boxes_keyboard(available, claimed_names, page=page, box_count=settings.box_count)


def boxes_title(settings) -> str:
    return f"🎁 {settings.box_count} TA QUTI"


@router.message(F.text == "🎁 Qutilarni ochish")
async def open_boxes(message: Message, session_factory, settings) -> None:
    markup = await build_boxes_keyboard(session_factory, settings)
    await message.answer(boxes_title(settings), reply_markup=markup)


@router.callback_query(F.data.startswith("boxes:page:"))
async def change_page(callback: CallbackQuery, session_factory, settings) -> None:
    try:
        page = int(callback.data.rsplit(":", 1)[1])
    except ValueError:
        await callback.answer()
        return
    page = min(max(page, 0), page_count(settings.box_count) - 1)
    markup = await build_boxes_keyboard(session_factory, settings, page=page)
    try:
        await callback.message.edit_reply_markup(reply_markup=markup)
    except TelegramBadRequest:
        pass  # "message is not modified" when the same page is pressed again
    await callback.answer()


@router.message(F.text == "⏳ Keyingi urinish")
async def next_attempt(message: Message, session_factory, settings, game_service: GameService) -> None:
    async with session_factory() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        last = None
        if user:
            last = await session.scalar(
                select(GameAttempt).where(GameAttempt.user_id == user.id).order_by(desc(GameAttempt.created_at)).limit(1)
            )
    last_created_at = as_utc(last.created_at) if last and last.created_at else None
    cooldown = timedelta(seconds=settings.cooldown_seconds)
    if not last_created_at or last_created_at + cooldown <= game_service.clock():
        markup = await build_boxes_keyboard(session_factory, settings)
        await message.answer("✅ Hozir quti tanlashingiz mumkin!", reply_markup=markup)
    else:
        next_allowed = last_created_at + cooldown
        await message.answer(f"⏳ Keyingi imkoniyat: {format_time(next_allowed)}\nQolgan vaqt: {remaining_text(next_allowed)}")


@router.callback_query(F.data == "box:unavailable")
async def unavailable_box(callback: CallbackQuery) -> None:
    await callback.answer("Bu quti allaqachon tanlangan.")


@router.callback_query(F.data.startswith("box:"))
async def choose_box(callback: CallbackQuery, session_factory, settings, game_service: GameService) -> None:
    await callback.answer()
    try:
        box_number = int(callback.data.split(":", 1)[1])
        async with session_factory() as session:
            result = await game_service.select_box(session, callback.from_user.id, box_number)
    except (ValueError, LookupError, PermissionError):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("⚠️ Bu so'rovni bajarib bo'lmadi.")
        return
    except Exception:
        await callback.message.answer("⚠️ Vaqtinchalik xatolik. Keyinroq qayta urinib ko'ring.")
        return
    await callback.message.edit_reply_markup(reply_markup=None)
    if result.finished:
        await callback.message.answer("🏆 Siz allaqachon pul yutug'ini topgansiz. Boshqa quti tanlay olmaysiz.")
    elif not result.accepted:
        await callback.message.answer(
            f"⏳ Siz hali quti tanlay olmaysiz.\nKeyingi imkoniyat: {format_time(result.next_allowed_at)}\n"
            f"Qolgan vaqt: {remaining_text(result.next_allowed_at)}"
        )
    elif result.attempt.is_winner:
        await callback.message.answer(
            f"🎉 TABRIKLAYMIZ!\n\nSiz <b>{box_number}-qutini</b> tanladingiz!\n\n"
            f"💰 Yutug'ingiz:\n<b>{format_money(result.attempt.gift_amount)}</b>\n\n🍀 Omad sizga kulib boqdi!"
        )
    else:
        await callback.message.answer(
            f"📦 Siz <b>{box_number}-qutini</b> tanladingiz.\n\nAfsuski, bu safar pul yutug'i chiqmadi 😔\n\n"
            f"🍀 Keyingi imkoniyatni {settings.cooldown_text}dan keyin sinab ko'ring!"
        )
