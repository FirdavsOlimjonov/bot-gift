from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def boxes_keyboard(available_numbers: list[int]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📦 {number}", callback_data=f"box:{number}") for number in available_numbers[start:start + 5]]
        for start in range(0, len(available_numbers), 5)
    ])
