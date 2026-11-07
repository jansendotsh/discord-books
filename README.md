# Discord Book Bot

A Discord bot for running a book club: track the current book, queue
upcoming picks, log reading progress, and rotate books with a single
admin command. Backed by a local SQLite database — no external sheets
or API keys beyond Discord.

## Features

- `/current` — show the current book with links
- `/next` — show the next upcoming book
- `/past` — list recent books (optional count, default 5, max 25)
- `/add` — add a book to the upcoming list (title, author, optional links)
- `/update` — log your progress as pages or a percentage
- `/progress` — show everyone's progress bars on the current book
- `/swap` *(admin)* — promote the next book to current and clear progress
- `/random` — pick a random upcoming book

## Requirements

- Python 3.12+
- `discord.py`, `aiosqlite`

## Configuration

Copy `.env.example` to `.env` and fill in the values:

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | yes | Discord bot token |
| `BOOK_CHANNEL_ID` | yes | Channel where commands are allowed |
| `BOOK_ROLE_ID` | yes | Role pinged by `/swap` |
| `ADMIN_IDS` | no | Comma-separated Discord user IDs who can run `/swap` |
| `DATABASE_PATH` | no | SQLite path (default `data/bookbot.db`) |

## Usage

### Local (Python)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit values
python -m bot
```

### Docker

```bash
cp .env.example .env  # then edit values
docker compose up -d --build
```

### systemd (Docker)

A sample unit file is provided as `systemd`. Install it with:

```bash
sudo cp systemd /etc/systemd/system/bookbot.service
sudo systemctl daemon-reload
sudo systemctl enable --now bookbot
```

The unit expects the repo at `/data/book-bot`, the database at
`/data/book-bot/data/bookbot.db`, and a `.env` file alongside the compose
file. The `docker compose` command must be available on the host.

## Migration from Google Sheets

This bot previously stored its data in a Google Sheet accessed via
`gspread`. As of 2.0 the data lives in a local SQLite database created
automatically on first run. To migrate existing data, export each sheet
tab to CSV and import into the `upcoming`, `past`, and `progress` tables
using any SQLite client.
