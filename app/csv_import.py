import csv
import io


def parse_discogs_csv(file_bytes: bytes) -> list[dict]:
    """Parse a Discogs "Export Collection" CSV into record dicts.

    Discogs exports don't include genre or purchase price, so those are
    left blank for the user to fill in (genre can later be backfilled via
    the Discogs API enrichment action).
    """
    text = file_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    rows = []
    for row in reader:
        artist = (row.get("Artist") or "").strip()
        title = (row.get("Title") or "").strip()
        if not artist or not title:
            continue

        release_id = None
        release_id_raw = (row.get("release_id") or "").strip()
        if release_id_raw.isdigit():
            release_id = int(release_id_raw)

        pressing_year = None
        year_raw = (row.get("Released") or "").strip()[:4]
        if year_raw.isdigit():
            pressing_year = int(year_raw)

        rows.append(
            {
                "artist": artist,
                "title": title,
                "label": (row.get("Label") or "").strip() or None,
                "pressing_year": pressing_year,
                "condition": (row.get("Collection Media Condition") or "").strip()
                or None,
                "sleeve_condition": (row.get("Collection Sleeve Condition") or "").strip()
                or None,
                "discogs_release_id": release_id,
                "notes": (row.get("Collection Notes") or "").strip() or None,
                "date_added": (row.get("Date Added") or "").strip() or None,
            }
        )
    return rows
