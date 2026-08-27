# Telegram 100 Box Game

Async Telegram bot built with Python 3.12, aiogram 3, SQLAlchemy 2 async, local SQLite, Alembic, and Pydantic Settings.

## Setup

1. Copy `.env.example` to `.env`.
2. Set `BOT_TOKEN` and comma-separated `ADMIN_IDS`. The default database is the local `box_game.db` file.
3. Install dependencies: `py -3.12 -m pip install -r requirements.txt`.
4. Apply the migration: `py -3.12 -m alembic upgrade head`.
5. Start the bot: `py -3.12 -m app.bot`.

On startup the bot also reconciles the 100 box rows with `WINNING_BOXES`. Each user's selection runs in an SQLite `BEGIN IMMEDIATE` transaction; the cooldown check, box claim, and attempt insert occur together. Once claimed, a box is removed from the selection keyboard for everyone and remains unavailable after a restart.

The bot resets the local database on every startup to begin a fresh game. This deletes all users, attempts, winners, and claimed boxes. A user who finds a money gift is marked as finished and cannot select another box during that game.

## Admin commands

`/admin` opens the admin panel for IDs in `ADMIN_IDS`.

`/box 25 10000` sets a prize. ` /remove_box 25` removes it. Admin callbacks show statistics, configured winning boxes, and paginated winners.

## Tests

`py -3.12 -m pytest`
