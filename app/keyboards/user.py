from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Qutilarni ochish")],
            [KeyboardButton(text="🏆 Mening yutuqlarim"), KeyboardButton(text="⏳ Keyingi urinish")],
            [KeyboardButton(text="ℹ️ Qoidalar")],
        ], resize_keyboard=True,
    )
