from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def boxes_keyboard(available_numbers: list[int], claimed_names: list[str | None] | None = None) -> InlineKeyboardMarkup:
    claimed_names = claimed_names or []
    buttons = [
        InlineKeyboardButton(text=f"📦 {number}", callback_data=f"box:{number}")
        if number in available_numbers
        else InlineKeyboardButton(text=claimed_names[number - 1] or "Noma'lum", callback_data="box:unavailable")
        for number in range(1, 101)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        buttons[start:start + 5]
        for start in range(0, 100, 5)
    ])
