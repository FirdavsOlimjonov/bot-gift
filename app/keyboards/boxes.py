from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def boxes_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📦 {number}", callback_data=f"box:{number}") for number in range(start, min(start + 5, 101))]
        for start in range(1, 101, 5)
    ])
