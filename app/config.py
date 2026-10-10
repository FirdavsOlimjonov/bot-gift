from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(alias="BOT_TOKEN")
    database_url: str = Field(default="sqlite+aiosqlite:///./box_game.db", alias="DATABASE_URL")
    admin_ids: str = Field(default="", alias="ADMIN_IDS")
    box_count: int = Field(default=200, alias="BOX_COUNT", ge=1)
    cooldown_seconds: int = Field(default=300, alias="COOLDOWN_SECONDS")
    winning_boxes: str = Field(default="", alias="WINNING_BOXES")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_id_set(self) -> set[int]:
        return {int(value.strip()) for value in self.admin_ids.split(",") if value.strip()}

    @property
    def configured_winning_boxes(self) -> dict[int, int]:
        result: dict[int, int] = {}
        for item in self.winning_boxes.split(","):
            if not item.strip():
                continue
            box_number, amount = item.split(":", 1)
            number = int(box_number)
            gift = int(amount)
            if not 1 <= number <= self.box_count or gift < 0:
                raise ValueError("WINNING_BOXES contains an invalid value")
            result[number] = gift
        return result

    @property
    def cooldown_text(self) -> str:
        minutes, seconds = divmod(self.cooldown_seconds, 60)
        if minutes and seconds:
            return f"{minutes} daqiqa {seconds} soniya"
        return f"{minutes} daqiqa" if minutes else f"{seconds} soniya"


@lru_cache
def get_settings() -> Settings:
    return Settings()
