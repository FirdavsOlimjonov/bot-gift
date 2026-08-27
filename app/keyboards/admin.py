from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Users", callback_data="admin:users"), InlineKeyboardButton(text="🎯 Game statistics", callback_data="admin:stats")],
        [InlineKeyboardButton(text="🏆 Winners", callback_data="admin:winners:0"), InlineKeyboardButton(text="📦 Box configuration", callback_data="admin:boxes")],
        [InlineKeyboardButton(text="📊 Reports", callback_data="admin:report:all")],
    ])
