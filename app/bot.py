import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from app.config import get_settings
from app.database.database import create_database
from app.database.models.base import Base
from app.handlers import admin, game, rules, start, stats
from app.services.game_service import GameService, initialize_boxes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main() -> None:
    load_dotenv()
    settings = get_settings()
    engine, session_factory = create_database(settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        await initialize_boxes(session, settings)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher["settings"] = settings
    dispatcher["session_factory"] = session_factory
    dispatcher["game_service"] = GameService(settings)
    dispatcher.include_routers(start.router, game.router, stats.router, rules.router, admin.router)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
