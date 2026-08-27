from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.keyboards.user import main_menu
from app.services.game_service import ensure_user

router = Router()

WELCOME = "🎁 100 BOX GAME\n\n100 ta quti ichida yashirin sovg'alar bor.\n\nHar 2 daqiqada 1 ta quti tanlashingiz mumkin.\n\nOmad sizga kulib boqsin! 🍀"


@router.message(CommandStart())
async def start(message: Message, session_factory) -> None:
    async with session_factory() as session:
        await ensure_user(session, message.from_user)
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer("Quti tanlang, natijani kuting va har 2 daqiqada qayta urinib ko'ring.", reply_markup=main_menu())
