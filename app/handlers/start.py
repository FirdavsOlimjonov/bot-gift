from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.keyboards.user import main_menu
from app.services.game_service import ensure_user

router = Router()


def welcome_text(settings) -> str:
    return (
        f"🎁 {settings.box_count} BOX GAME\n\n"
        f"{settings.box_count} ta quti ichida yashirin sovg'alar bor.\n\n"
        f"Har {settings.cooldown_text}da 1 ta quti tanlashingiz mumkin.\n\n"
        "Omad sizga kulib boqsin! 🍀"
    )


@router.message(CommandStart())
async def start(message: Message, session_factory, settings) -> None:
    async with session_factory() as session:
        await ensure_user(session, message.from_user)
    await message.answer(welcome_text(settings), reply_markup=main_menu())


@router.message(Command("help"))
async def help_command(message: Message, settings) -> None:
    await message.answer(
        f"Quti tanlang, natijani kuting va har {settings.cooldown_text}da qayta urinib ko'ring.",
        reply_markup=main_menu(),
    )
