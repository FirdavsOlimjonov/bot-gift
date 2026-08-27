from datetime import datetime, timezone


def format_money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " so'm"


def remaining_text(next_allowed_at: datetime | None) -> str:
    if next_allowed_at is None:
        return "Hozir"
    seconds = max(0, int((next_allowed_at - datetime.now(timezone.utc)).total_seconds()))
    return f"{seconds // 60} daqiqa {seconds % 60} soniya"


def format_time(value: datetime) -> str:
    return value.astimezone().strftime("%H:%M:%S")
