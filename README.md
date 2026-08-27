# Telegram 100 Box Game

Async Telegram bot built with Python 3.12, aiogram 3, SQLAlchemy 2 async, PostgreSQL, asyncpg, Alembic, and Pydantic Settings.

## Setup

1. Create a PostgreSQL database and copy `.env.example` to `.env`.
2. Set `BOT_TOKEN`, `DATABASE_URL`, and comma-separated `ADMIN_IDS`.
3. Install dependencies: `py -3.12 -m pip install -r requirements.txt`.
4. Apply the migration: `py -3.12 -m alembic upgrade head`.
5. Start the bot: `py -3.12 -m app.bot`.

On startup the bot also reconciles the 100 box rows with `WINNING_BOXES`. Each user's selection locks that user's PostgreSQL row with `SELECT FOR UPDATE`; the cooldown check and attempt insert occur in one transaction. The same box can therefore be selected by different users.

## Admin commands

`/admin` opens the admin panel for IDs in `ADMIN_IDS`.

`/box 25 10000` sets a prize. ` /remove_box 25` removes it. Admin callbacks show statistics, configured winning boxes, and paginated winners.

## Tests

`py -3.12 -m pytest`
