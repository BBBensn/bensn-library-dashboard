import hmac
import os
from datetime import datetime

import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://bensn:CHANGE_ME@localhost:5432/bensnos",
)
LIBRARY_SYNC_KEY = os.environ.get("LIBRARY_SYNC_KEY", "CHANGE_ME")

WISHLIST_TYPES = {"movie", "series"}
WISHLIST_PRIORITIES = {"low", "medium", "high"}
WISHLIST_STATUSES = {"open", "in_progress", "done"}

LIBRARY_ITEM_FIELDS = [
    "jellyfin_id", "item_type", "title", "series_title", "series_jellyfin_id",
    "season_number", "episode_number", "year", "container", "video_codec",
    "audio_codec", "audio_languages", "resolution", "file_size_bytes",
]


def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


def db_query(sql, params=None, fetchone=False, commit=False):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.rowcount
        return cur.fetchone() if fetchone else cur.fetchall()
    finally:
        conn.close()


def db_insert(sql, params):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        result = cur.fetchone()
        conn.commit()
        return result
    finally:
        conn.close()


def serialize(row):
    if row is None:
        return None
    out = dict(row)
    for key, value in out.items():
        if isinstance(value, datetime):
            out[key] = value.isoformat()
    return out


def serialize_list(rows):
    return [serialize(row) for row in rows]


# ── Wishlist ─────────────────────────────────────────────────────────────

@app.route("/api/wishlist", methods=["GET"])
def wishlist_list():
    rows = db_query("SELECT * FROM wishlist_items ORDER BY created_at DESC")
    return jsonify(serialize_list(rows))


@app.route("/api/wishlist", methods=["POST"])
def wishlist_create():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    item_type = data.get("type") if data.get("type") in WISHLIST_TYPES else None
    priority = data.get("priority") if data.get("priority") in WISHLIST_PRIORITIES else "low"

    row = db_insert(
        """
        INSERT INTO wishlist_items (title, type, requested_by, note, priority)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        (title, item_type, data.get("requested_by"), data.get("note"), priority),
    )
    return jsonify(serialize(row)), 201


@app.route("/api/wishlist/<int:item_id>/status", methods=["PATCH"])
def wishlist_update_status(item_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in WISHLIST_STATUSES:
        return jsonify({"error": "invalid status"}), 400

    row = db_insert(
        "UPDATE wishlist_items SET status = %s WHERE id = %s RETURNING *",
        (status, item_id),
    )
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(serialize(row))


# ── Library / Bestandsliste ─────────────────────────────────────────────

@app.route("/api/library", methods=["GET"])
def library_list():
    rows = db_query("SELECT * FROM library_items ORDER BY title ASC")

    movies = []
    series_map = {}

    for row in rows:
        item = serialize(row)
        if item["item_type"] == "movie":
            movies.append(item)
            continue

        series_id = item["series_jellyfin_id"]
        series = series_map.setdefault(series_id, {
            "series_title": item["series_title"],
            "series_jellyfin_id": series_id,
            "episode_count": 0,
            "total_size_bytes": 0,
            "seasons": {},
        })
        season_number = item["season_number"]
        season = series["seasons"].setdefault(season_number, {
            "season_number": season_number,
            "episode_count": 0,
            "total_size_bytes": 0,
            "episodes": [],
        })

        size = item["file_size_bytes"] or 0
        season["episode_count"] += 1
        season["total_size_bytes"] += size
        series["episode_count"] += 1
        series["total_size_bytes"] += size
        season["episodes"].append(item)

    series_list = []
    for series in series_map.values():
        series["seasons"] = sorted(series["seasons"].values(), key=lambda s: (s["season_number"] is None, s["season_number"]))
        for season in series["seasons"]:
            season["episodes"].sort(key=lambda e: (e["episode_number"] is None, e["episode_number"]))
        series_list.append(series)
    series_list.sort(key=lambda s: s["series_title"] or "")

    return jsonify({"movies": movies, "series": series_list})


@app.route("/api/library/sync", methods=["POST"])
def library_sync():
    key = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(key, LIBRARY_SYNC_KEY):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    items = data.get("items")
    if not isinstance(items, list):
        return jsonify({"error": "items must be a list"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM library_items")
        for item in items:
            values = [item.get(field) for field in LIBRARY_ITEM_FIELDS]
            cur.execute(
                f"""
                INSERT INTO library_items ({", ".join(LIBRARY_ITEM_FIELDS)})
                VALUES ({", ".join(["%s"] * len(LIBRARY_ITEM_FIELDS))})
                """,
                values,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify({"synced": len(items)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5006)
