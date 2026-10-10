# CLAUDE.md — bot-gift (Telegram "Box Game", 200 boxes)

Project notes for Claude. Read this first; it replaces re-learning the codebase.
Last full review: 2026-10-10 (after the 200-box change). If files changed since then, re-read only the changed ones.

## What it is
Async Telegram bot: users pick 1 of `BOX_COUNT` boxes (now **200**, 20 prizes, 5-min cooldown since 2026-10-10); some boxes hide money prizes (so'm).
Each box can be claimed once (by anyone). Per-user cooldown between picks. A user who wins money is "finished" and can't pick again.
UI text is in **Uzbek (Latin)**; admin panel text is mostly English.
Repo: https://github.com/FirdavsOlimjonov/bot-gift (branch `main`). Local path: `D:\bot-gift` (Windows).

## Stack
Python 3.12 · aiogram 3 · SQLAlchemy 2 (async) · aiosqlite (local SQLite `box_game.db`) · Alembic · pydantic-settings · pytest + pytest-asyncio (`asyncio_mode = auto`).

## Commands (Windows)
- Install: `py -3.12 -m pip install -r requirements.txt`
- Run: `py -3.12 -m app.bot`
- Tests: `py -3.12 -m pytest`
- Migrations: `py -3.12 -m alembic upgrade head` (see caveat below — effectively unused at runtime)

## Config (`.env`, see `.env.example`; loaded by `app/config.py` Settings)
| Var | Default | Notes |
|---|---|---|
| `BOT_TOKEN` | required | |
| `DATABASE_URL` | `sqlite+aiosqlite:///./box_game.db` | |
| `ADMIN_IDS` | "" | comma-separated Telegram IDs → `settings.admin_id_set` |
| `BOX_COUNT` | 200 | number of boxes; all range checks use it |
| `COOLDOWN_SECONDS` | 300 | `settings.cooldown_text` → "5 daqiqa" for UI text |
| `WINNING_BOXES` | "" | `num:amount,...` e.g. `25:10000,54:7000` → `settings.configured_winning_boxes` (validates 1..BOX_COUNT, amount ≥ 0) |
`get_settings()` is `lru_cache`d.

## Layout
```
app/
  bot.py            entrypoint: load_dotenv → create_database → reset_database (DROP+CREATE ALL!) → initialize_boxes → polling
                    DI via dispatcher["settings"], ["session_factory"], ["game_service"]; default parse_mode=HTML
                    router order: start, game, stats, rules, admin
  config.py         Settings (above)
  utils.py          format_money ("10 000 so'm"), as_utc, remaining_text ("X daqiqa Y soniya"/"Hozir"), format_time (HH:MM:SS local)
  database/
    database.py     create_database(settings) -> (engine, async_sessionmaker expire_on_commit=False); sqlite timeout=30; reset_database(engine)
    models/
      user.py       Base(DeclarativeBase) is defined HERE; User: id, telegram_id(unique BigInt), username, first_name, last_name, created_at, updated_at, is_blocked, has_won
      box.py        Box: id, box_number(>=1, unique), gift_amount(>=0), is_winner, is_available, selected_by_name, timestamps
      game_attempt.py GameAttempt: id, user_id(FK users, cascade), box_number, gift_amount, is_winner, created_at(indexed)
      base.py       re-exports Base from user.py
  services/
    game_service.py GameService(settings, clock=None).select_box(session, telegram_id, box_number) -> SelectionResult(accepted, attempt, next_allowed_at, finished)
                    initialize_boxes(session, settings): ensures BOX_COUNT rows, applies WINNING_BOXES
                    ensure_user(session, tg_user): upsert user on /start
                    winning_amount(session, telegram_id) -> prize int if user.has_won else None; won_text(amount) -> "🏆 Bo'ldi, siz allaqachon yutgansiz!..."
    statistics_service.py user_statistics(session, user_id), admin_statistics(session)
  handlers/
    start.py        /start (ensure_user + main menu), /help
    game.py         "🎁 Qutilarni ochish" (paged box keyboard), "⏳ Keyingi urinish" (cooldown status), callbacks "box:<n>", "box:unavailable", "boxes:page:<i>"; build_boxes_keyboard() helper
    stats.py        /stats and "🏆 Mening yutuqlarim"
    rules.py        "ℹ️ Qoidalar"
    admin.py        /admin, /box <n> <amount>, /remove_box <n>; callbacks admin:stats|users|boxes|report:<period>|winners:<page>
  keyboards/
    user.py         main_menu() reply keyboard (4 buttons — handlers match on exact emoji text)
    boxes.py        boxes_keyboard(available, claimed_names, page, box_count): PAGE_SIZE=50 (10 rows × 5) + a page-jump row ("1-50", "• 51-100 •"...). Telegram max 100 buttons per inline keyboard → never exceed that. Claimed boxes show claimer's name
    admin.py        admin_keyboard() inline
migrations/         alembic, versions 0001_initial → 0002_box_availability → 0003_box_selector_name → 0004_user_has_won
                    env.py strips "+aiosqlite" from URL for sync alembic
tests/test_game_handler.py  calls choose_box with fake aiogram callback objects (no /start, winner blocked, taken box)
tests/test_game_service.py  in-memory sqlite; tests cooldown (5 min boundary), 200 boxes, keyboard page limits, win/lose, finished-after-win, box claim exclusivity, stats, is_admin
```

## Core game logic (`GameService.select_box`)
One transaction (`session.begin()`, plus `BEGIN IMMEDIATE` on SQLite for write lock):
1. Validate 1..BOX_COUNT (else `ValueError`).
2. Load user (`with_for_update`); missing/blocked → `PermissionError`; `has_won` → `SelectionResult(False, finished=True)`.
3. Cooldown: last attempt `created_at + cooldown > now` → `SelectionResult(False, next_allowed_at=...)`. Naive datetimes treated as UTC.
4. Load box; missing → `LookupError`; `not is_available` → `ValueError("Box is no longer available")`.
5. Mark box unavailable, set `selected_by_name` (first_name / username / "Noma'lum"); if winner → `user.has_won = True`.
6. Insert GameAttempt with `created_at=now` (clock injectable for tests).
Handler `choose_box` first calls `ensure_user(callback.from_user)` (users are wiped on restart; without this, clicking a box before /start raised PermissionError → "Bu so'rovni bajarib bo'lmadi" — bug fixed 2026-10-10). Errors: taken box → "❌ Bu quti allaqachon tanlangan" + refreshed keyboard; blocked → "⛔"; anything else logged via `logger.exception`.

## Important behaviors / gotchas
- **DB is wiped on every startup** (`reset_database` = drop_all + create_all). Each restart = fresh game. Alembic migrations are therefore not what builds the schema at runtime; keep models and migrations in sync anyway.
- **Admin `/box` and `/remove_box` changes are lost on restart** — startup re-applies `WINNING_BOXES` from `.env`.
- `Base` lives in `models/user.py` (unusual); import via `app.database.models.base`.
- Handlers get dependencies by parameter name injection from dispatcher: `settings`, `session_factory`, `game_service`.
- Admin check = `is_admin(obj, settings.admin_id_set)` on every admin handler/callback.
- **Winners are done for the game**: after a win, "🎁 Qutilarni ochish", "⏳ Keyingi urinish" and box callbacks all reply with `won_text(...)` (no keyboard, no countdown); stats shows "Keyingi urinish: Yo'q — siz allaqachon yutgansiz". Enforced in `select_box` (`has_won`) + handler checks via `winning_amount`.

## Known issues
Fixed 2026-10-10: `next_attempt` NameError (Box import), cooldown text mismatch (now from settings everywhere), Markdown `**` → HTML `<b>`, rules text claiming results are hidden.
Still open:
1. Model CHECK changed to `box_number >= 1`, but no Alembic migration added (0001 still has BETWEEN 1 AND 100). Irrelevant at runtime because startup does drop_all/create_all; add a migration if Alembic is ever used for real.
2. `stats.py` shows "Tanlangan qutilar" = same number as attempts (duplicate).
3. Admin "📊 Reports" button only sends `admin:report:all`; `today/yesterday/7d/30d` have no buttons. "yesterday" = last 24h.
4. `requirements.txt` pins `pytest<9` but pytest 9 was used locally.
5. Tests' `Settings(...)` also reads the real `.env`; always pass explicit values in tests.

## Current prize setup (.env, set by user 2026-10-10)
BOX_COUNT=200, COOLDOWN_SECONDS=300, 20 prizes, total exactly 300 000 so'm (box 7 = 500 is fixed by user, don't change it):
`7:500,13:14000,14:24000,21:16000,37:15000,53:13000,61:17500,72:17500,89:11000,95:21000,103:14000,119:11000,127:17500,138:1000,145:21000,152:13000,166:16000,171:24500,184:15000,199:17500`
.env can't be written via remote tools — user edits it by hand.

## Conventions
- Money formatted via `format_money`; times via `format_time` / `remaining_text`.
- User-facing strings in Uzbek; keep emoji prefixes since reply-keyboard handlers match exact text (change keyboard + handler together).
- Keep business logic in `services/`, handlers thin; make new logic testable with injectable clock and in-memory SQLite like existing tests.
- Don't commit `.env` or `box_game.db` (gitignored).
- Before committing to D:\bot-gift, stage + diff the device copy first: the user's IDE (PyCharm) once silently reverted game.py to an older version.
