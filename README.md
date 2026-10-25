# Vinyl Tracker

A personal vinyl record collection tracker built with FastAPI, SQLite, and server-rendered Jinja2 templates.

## Features

- Log records with artist, title, label, genre, pressing year, condition, and purchase price
- Search across artist/title/label, filter by genre, sort by artist/year/price/date added
- Total collection value + a stats page with value broken down by genre
- A wishlist for records you want but don't own yet, with a one-click "Move to Collection" once bought
- A settings page to pick your collection's currency (defaults to INR)
- Look up a release on Discogs when adding a record — search by artist/title or paste a release URL/ID — to autofill artist, title, label, genre, year, and cover art
- Import a Discogs "Export Collection" CSV (artist, title, label, year, condition, release ID)
- Optional enrichment: pull genre and cover art from the Discogs API using the release ID

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

(Optional) Copy `.env.example` to `.env` and set `DISCOGS_TOKEN` to a personal access token from
https://www.discogs.com/settings/developers. Enrichment and pasting a release URL/ID work without a token (just at a lower rate limit); searching Discogs by artist/title when adding a record requires a token, since that endpoint needs authentication.

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
