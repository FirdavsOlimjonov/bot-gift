from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.text == "ℹ️ Qoidalar")
async def rules(message: Message, settings) -> None:
    await message.answer(
        "📜 O'YIN QOIDALARI\n\n"
        f"1. Har bir foydalanuvchi har {settings.cooldown_text}da 1 ta quti tanlashi mumkin.\n"
        "2. Bir urinishda faqat 1 ta quti tanlash mumkin.\n"
        f"3. Jami {settings.box_count} ta quti bor, har birining o'z natijasi mavjud.\n"
        "4. Ba'zi qutilarda pul yutug'i mavjud.\n"
        "5. Yutuqlar tizim tomonidan avtomatik aniqlanadi.\n"
        "6. Pul yutug'ini topgan foydalanuvchi boshqa quti tanlay olmaydi.\n"
        "7. Yutuqlar bo'yicha yakuniy ma'lumot admin panelida ko'rsatiladi."
    )
