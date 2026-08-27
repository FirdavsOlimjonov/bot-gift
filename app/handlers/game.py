from aiogram import F, Router
from datetime import timedelta

from aiogram.types import CallbackQuery, Message

from app.keyboards.boxes import boxes_keyboard
from app.services.game_service import GameService
from app.utils import as_utc, format_money, format_time, remaining_text

router = Router()


@router.message(F.text == "🎁 Qutilarni ochish")
async def open_boxes(message: Message, session_factory) -> None:
    from sqlalchemy import select
    from app.database.models import Box

    async with session_factory() as session:
        boxes = (await session.scalars(select(Box).order_by(Box.box_number))).all()
    available = [box.box_number for box in boxes if box.is_available]
    claimed_names = [box.selected_by_name for box in boxes]
    await message.answer("🎁 100 TA QUTI", reply_markup=boxes_keyboard(available, claimed_names))


@router.message(F.text == "⏳ Keyingi urinish")
async def next_attempt(message: Message, session_factory, game_service: GameService) -> None:
    async with session_factory() as session:
        from app.database.models import User
        from sqlalchemy import select
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        last = None
        if user:
            from sqlalchemy import desc
            from app.database.models import GameAttempt
            last = await session.scalar(select(GameAttempt).where(GameAttempt.user_id == user.id).order_by(desc(GameAttempt.created_at)).limit(1))
    last_created_at = as_utc(last.created_at) if last and last.created_at else None
    if not last_created_at or last_created_at + timedelta(seconds=game_service.settings.cooldown_seconds) <= game_service.clock():
        async with session_factory() as session:
            boxes = (await session.scalars(select(Box).order_by(Box.box_number))).all()
        available = [box.box_number for box in boxes if box.is_available]
        claimed_names = [box.selected_by_name for box in boxes]
        await message.answer("✅ Hozir quti tanlashingiz mumkin!", reply_markup=boxes_keyboard(available, claimed_names))
    else:
        next_allowed = last_created_at + timedelta(seconds=game_service.settings.cooldown_seconds)
        await message.answer(f"⏳ Keyingi imkoniyat: {format_time(next_allowed)}\nQolgan vaqt: {remaining_text(next_allowed)}")


@router.callback_query(F.data.startswith("box:"))
async def choose_box(callback: CallbackQuery, session_factory, game_service: GameService) -> None:
    await callback.answer()
    if callback.data == "box:unavailable":
        return
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
    if not result.accepted:
        await callback.message.answer(f"⏳ Siz hali quti tanlay olmaysiz.\nKeyingi imkoniyat: {format_time(result.next_allowed_at)}\nQolgan vaqt: {remaining_text(result.next_allowed_at)}")
    elif result.attempt.is_winner:
        await callback.message.answer(f"🎉 TABRIKLAYMIZ!\n\nSiz **{box_number}-qutini** tanladingiz!\n\n💰 Yutug'ingiz:\n**{format_money(result.attempt.gift_amount)}**\n\n🍀 Omad sizga kulib boqdi!", parse_mode="Markdown")
    else:
        await callback.message.answer(f"📦 Siz **{box_number}-qutini** tanladingiz.\n\nAfsuski, bu safar pul yutug'i chiqmadi 😔\n\n🍀 Keyingi imkoniyatni 2 daqiqadan keyin sinab ko'ring!", parse_mode="Markdown")


@router.callback_query(F.data == "box:unavailable")
async def unavailable_box(callback: CallbackQuery) -> None:
    await callback.answer("Bu quti allaqachon tanlangan.")
