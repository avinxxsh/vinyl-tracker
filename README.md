# Vinyl Tracker

A personal vinyl record collection tracker built with FastAPI, SQLite, and server-rendered Jinja2 templates.

## Features

- Log records with artist, title, label, genre, pressing year, condition, and purchase price
- Search across artist/title/label, filter by genre, sort by artist/year/price/date added
- Total collection value + a stats page with value broken down by genre
- Import a Discogs "Export Collection" CSV (artist, title, label, year, condition, release ID)
- Optional enrichment: pull genre and cover art from the Discogs API using the release ID

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

(Optional) Copy `.env.example` to `.env` and set `DISCOGS_TOKEN` to a personal access token from
https://www.discogs.com/settings/developers for higher API rate limits during enrichment. It works without a token too, just slower.

## Run

```bash
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000

The SQLite database (`vinyl.db`) is created automatically on first run.

## Importing your Discogs collection

1. On discogs.com, go to **Collection &rarr; Export Collection** and download the CSV.
2. In the app, go to **Import CSV** and upload the file.
3. Discogs exports don't include genre or purchase price, so those come in blank. Fill in purchase price by hand (it's yours to know), and use **Fetch missing covers/genres from Discogs** on the collection page to backfill genre and cover art from the Discogs API.
