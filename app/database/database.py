from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings


def create_database(settings: Settings) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    connect_args = {"timeout": 30} if settings.database_url.startswith("sqlite") else {}
    engine = create_async_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


async def reset_database(engine: AsyncEngine) -> None:
    from app.database.models.base import Base

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
