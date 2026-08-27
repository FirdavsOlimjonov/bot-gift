from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.text == "ℹ️ Qoidalar")
async def rules(message: Message) -> None:
    await message.answer("📜 O'YIN QOIDALARI\n\n1. Har bir foydalanuvchi har 2 daqiqada 1 ta quti tanlashi mumkin.\n2. Bir urinishda faqat 1 ta quti tanlash mumkin.\n3. Har bir qutining o'z natijasi mavjud.\n4. Ba'zi qutilarda pul yutug'i mavjud.\n5. Yutuqlar tizim tomonidan avtomatik aniqlanadi.\n6. Boshqa foydalanuvchilarning natijalarini ko'rish mumkin emas.\n7. Yutuqlar bo'yicha yakuniy ma'lumot admin panelida ko'rsatiladi.")
