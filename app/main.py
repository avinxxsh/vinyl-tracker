import time

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import csv_import, discogs, models
from app.database import Base, SessionLocal, engine

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vinyl Tracker")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SORT_OPTIONS = {
    "artist": (models.Record.artist.asc(), "Artist"),
    "year": (models.Record.pressing_year.desc(), "Year (newest)"),
    "price": (models.Record.purchase_price.desc(), "Price (highest)"),
    "added": (models.Record.id.desc(), "Recently added"),
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_int(value: str) -> int | None:
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


def to_float(value: str) -> float | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def record_from_form(
    artist, title, label, genre, pressing_year, condition,
    sleeve_condition, purchase_price, discogs_release_id, notes,
) -> dict:
    return {
        "artist": artist.strip(),
        "title": title.strip(),
        "label": label.strip() or None,
        "genre": genre.strip() or None,
        "pressing_year": to_int(pressing_year),
        "condition": condition.strip() or None,
        "sleeve_condition": sleeve_condition.strip() or None,
        "purchase_price": to_float(purchase_price),
        "discogs_release_id": to_int(discogs_release_id),
        "notes": notes.strip() or None,
    }


@app.get("/")
def index(
    request: Request,
    q: str = "",
    genre: str = "",
    sort: str = "artist",
    db: Session = Depends(get_db),
):
    query = db.query(models.Record)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.Record.artist.ilike(like),
                models.Record.title.ilike(like),
                models.Record.label.ilike(like),
            )
        )
    if genre:
        query = query.filter(models.Record.genre == genre)

    order_clause, _ = SORT_OPTIONS.get(sort, SORT_OPTIONS["artist"])
    records = query.order_by(order_clause).all()

    total_value = sum(r.purchase_price or 0 for r in records)

    genres = [
        g[0]
        for g in db.query(models.Record.genre)
        .filter(models.Record.genre.isnot(None), models.Record.genre != "")
        .distinct()
        .order_by(models.Record.genre)
        .all()
    ]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "records": records,
            "q": q,
            "genre": genre,
            "sort": sort,
            "sort_options": SORT_OPTIONS,
            "genres": genres,
            "total_value": total_value,
            "count": len(records),
        },
    )


@app.get("/stats")
def stats(request: Request, db: Session = Depends(get_db)):
    records = db.query(models.Record).all()
    count = len(records)
    total_value = sum(r.purchase_price or 0 for r in records)
    avg_price = total_value / count if count else 0

    by_genre: dict[str, dict] = {}
    for r in records:
        g = r.genre or "Unknown"
        entry = by_genre.setdefault(g, {"count": 0, "value": 0.0})
        entry["count"] += 1
        entry["value"] += r.purchase_price or 0
    by_genre = dict(sorted(by_genre.items(), key=lambda kv: kv[1]["value"], reverse=True))

    missing_covers = sum(1 for r in records if r.discogs_release_id and not r.cover_url)

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "count": count,
            "total_value": total_value,
            "avg_price": avg_price,
            "by_genre": by_genre,
            "missing_covers": missing_covers,
        },
    )


@app.get("/records/new")
def new_record_form(request: Request):
    return templates.TemplateResponse(
        "record_form.html", {"request": request, "record": None, "action": "/records"}
    )


@app.post("/records")
def create_record(
    artist: str = Form(...),
    title: str = Form(...),
    label: str = Form(""),
    genre: str = Form(""),
    pressing_year: str = Form(""),
    condition: str = Form(""),
    sleeve_condition: str = Form(""),
    purchase_price: str = Form(""),
    discogs_release_id: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    data = record_from_form(
        artist, title, label, genre, pressing_year, condition,
        sleeve_condition, purchase_price, discogs_release_id, notes,
    )
    db.add(models.Record(**data))
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/records/{record_id}/edit")
def edit_record_form(record_id: int, request: Request, db: Session = Depends(get_db)):
    record = db.get(models.Record, record_id)
    return templates.TemplateResponse(
        "record_form.html",
        {"request": request, "record": record, "action": f"/records/{record_id}/update"},
    )


@app.post("/records/{record_id}/update")
def update_record(
    record_id: int,
    artist: str = Form(...),
    title: str = Form(...),
    label: str = Form(""),
    genre: str = Form(""),
    pressing_year: str = Form(""),
    condition: str = Form(""),
    sleeve_condition: str = Form(""),
    purchase_price: str = Form(""),
    discogs_release_id: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    record = db.get(models.Record, record_id)
    data = record_from_form(
        artist, title, label, genre, pressing_year, condition,
        sleeve_condition, purchase_price, discogs_release_id, notes,
    )
    for key, value in data.items():
        setattr(record, key, value)
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/records/{record_id}/delete")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.get(models.Record, record_id)
    if record:
        db.delete(record)
        db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/records/{record_id}/enrich")
def enrich_record(record_id: int, db: Session = Depends(get_db)):
    record = db.get(models.Record, record_id)
    if record and record.discogs_release_id:
        data = discogs.fetch_release(record.discogs_release_id)
        if data:
            if data.get("genre"):
                record.genre = data["genre"]
            if data.get("cover_url"):
                record.cover_url = data["cover_url"]
            if not record.label and data.get("label"):
                record.label = data["label"]
            if not record.pressing_year and data.get("pressing_year"):
                record.pressing_year = data["pressing_year"]
            db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/enrich-missing")
def enrich_missing(db: Session = Depends(get_db)):
    records = (
        db.query(models.Record)
        .filter(models.Record.discogs_release_id.isnot(None))
        .filter(
            or_(models.Record.cover_url.is_(None), models.Record.genre.is_(None))
        )
        .limit(25)
        .all()
    )
    updated = 0
    for i, record in enumerate(records):
        data = discogs.fetch_release(record.discogs_release_id)
        if data:
            if data.get("genre") and not record.genre:
                record.genre = data["genre"]
            if data.get("cover_url"):
                record.cover_url = data["cover_url"]
            updated += 1
        if i < len(records) - 1:
            time.sleep(1.1)  # stay under Discogs' rate limit
    db.commit()
    return RedirectResponse(f"/?enriched={updated}", status_code=303)


@app.get("/import")
def import_form(request: Request):
    return templates.TemplateResponse("import.html", {"request": request})


@app.post("/import")
async def import_csv(
    request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    content = await file.read()
    rows = csv_import.parse_discogs_csv(content)

    existing_ids = {
        r[0]
        for r in db.query(models.Record.discogs_release_id)
        .filter(models.Record.discogs_release_id.isnot(None))
        .all()
    }

    imported = 0
    skipped = 0
    for row in rows:
        rid = row["discogs_release_id"]
        if rid and rid in existing_ids:
            skipped += 1
            continue
        db.add(models.Record(**row))
        if rid:
            existing_ids.add(rid)
        imported += 1
    db.commit()

    return templates.TemplateResponse(
        "import.html",
        {"request": request, "imported": imported, "skipped": skipped, "total": len(rows)},
    )
