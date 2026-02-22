# Telegram bot

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r tg/requirements.txt
   ```
3. Create `tg/.env` from `tg/.env.example` and set:
   - `BOT_TOKEN`
   - `ADMIN_ID`
   - optional `DB_PATH`

For API/admin settings use root `.env.example`.

## Migrations

Apply schema migrations:

```bash
python tg/migrations/runner.py upgrade
```

Check status:

```bash
python tg/migrations/runner.py status
```

Rollback one revision:

```bash
python tg/migrations/runner.py downgrade --steps 1
```

## Run

```bash
python tg/main.py
```

Run admin backend API:

```bash
python tg/server.py
```

## Data

- Default SQLite path is `tg/data/applications.db`.
- If legacy `tg/applications.db` already exists, bot keeps using it until you set `DB_PATH`.
- Keep this file out of version control.
