from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Telegram allows at most 100 buttons per inline keyboard, so boxes are shown in pages.
PAGE_SIZE = 50
ROW_SIZE = 5


def page_count(box_count: int) -> int:
    return max(1, ceil(box_count / PAGE_SIZE))


def boxes_keyboard(
    available_numbers: list[int],
    claimed_names: list[str | None] | None = None,
    page: int = 0,
    box_count: int = 200,
) -> InlineKeyboardMarkup:
    claimed_names = claimed_names or []
    available = set(available_numbers)
    pages = page_count(box_count)
    page = min(max(page, 0), pages - 1)
    first = page * PAGE_SIZE + 1
    last = min(first + PAGE_SIZE - 1, box_count)

    buttons = []
    for number in range(first, last + 1):
        if number in available:
            buttons.append(InlineKeyboardButton(text=f"📦 {number}", callback_data=f"box:{number}"))
        else:
            name = claimed_names[number - 1] if number - 1 < len(claimed_names) else None
            buttons.append(InlineKeyboardButton(text=name or "Noma'lum", callback_data="box:unavailable"))

    rows = [buttons[start:start + ROW_SIZE] for start in range(0, len(buttons), ROW_SIZE)]

    if pages > 1:
        navigation = []
        for index in range(pages):
            start = index * PAGE_SIZE + 1
            end = min(start + PAGE_SIZE - 1, box_count)
            label = f"{start}-{end}"
            if index == page:
                label = f"• {label} •"
            navigation.append(InlineKeyboardButton(text=label, callback_data=f"boxes:page:{index}"))
        rows.append(navigation)

    return InlineKeyboardMarkup(inline_keyboard=rows)
