#!/usr/bin/env python3
"""Nightly sync: Jellyfin-Bestand -> library.bensn.me.

Laeuft auf der NAS via TrueNAS Cron Job, stdlib-only (kein pip install noetig).
Konfiguration ueber Umgebungsvariablen (im Cron-Job-Befehl setzen).
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

JELLYFIN_URL = os.environ.get("JELLYFIN_URL", "http://127.0.0.1:30013")
JELLYFIN_API_KEY = os.environ.get("JELLYFIN_API_KEY", "CHANGE_ME")
LIBRARY_API_URL = os.environ.get("LIBRARY_API_URL", "https://library.bensn.me/api/library/sync")
LIBRARY_SYNC_KEY = os.environ.get("LIBRARY_SYNC_KEY", "CHANGE_ME")


def jellyfin_get(path, params):
    query = urllib.parse.urlencode(params)
    url = f"{JELLYFIN_URL}{path}?{query}"
    req = urllib.request.Request(url, headers={"X-Emby-Token": JELLYFIN_API_KEY})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def extract_media(item):
    sources = item.get("MediaSources") or []
    source = sources[0] if sources else {}
    streams = source.get("MediaStreams") or []

    video = next((s for s in streams if s.get("Type") == "Video"), {})
    audio_streams = [s for s in streams if s.get("Type") == "Audio"]

    resolution = None
    if video.get("Width") and video.get("Height"):
        resolution = f"{video['Width']}x{video['Height']}"

    languages = []
    for s in audio_streams:
        lang = s.get("Language")
        if lang and lang not in languages:
            languages.append(lang)

    return {
        "container": source.get("Container"),
        "video_codec": video.get("Codec"),
        "audio_codec": audio_streams[0].get("Codec") if audio_streams else None,
        "audio_languages": ", ".join(languages) if languages else None,
        "resolution": resolution,
        "file_size_bytes": source.get("Size"),
    }


def fetch_movies():
    data = jellyfin_get("/Items", {
        "Recursive": "true",
        "IncludeItemTypes": "Movie",
        "Fields": "MediaSources,ProductionYear",
    })
    items = []
    for item in data.get("Items", []):
        items.append({
            "jellyfin_id": item["Id"],
            "item_type": "movie",
            "title": item.get("Name"),
            "series_title": None,
            "series_jellyfin_id": None,
            "season_number": None,
            "episode_number": None,
            "year": item.get("ProductionYear"),
            **extract_media(item),
        })
    return items


def fetch_episodes():
    data = jellyfin_get("/Items", {
        "Recursive": "true",
        "IncludeItemTypes": "Episode",
        "Fields": "MediaSources,ProductionYear,ParentIndexNumber,IndexNumber,SeriesName,SeriesId",
    })
    items = []
    for item in data.get("Items", []):
        items.append({
            "jellyfin_id": item["Id"],
            "item_type": "episode",
            "title": item.get("Name"),
            "series_title": item.get("SeriesName"),
            "series_jellyfin_id": item.get("SeriesId"),
            "season_number": item.get("ParentIndexNumber"),
            "episode_number": item.get("IndexNumber"),
            "year": item.get("ProductionYear"),
            **extract_media(item),
        })
    return items


def main():
    items = fetch_movies() + fetch_episodes()
    movie_count = sum(1 for i in items if i["item_type"] == "movie")
    episode_count = sum(1 for i in items if i["item_type"] == "episode")
    print(f"{len(items)} Items gefunden ({movie_count} Filme, {episode_count} Episoden)")

    body = json.dumps({"items": items}).encode("utf-8")
    req = urllib.request.Request(
        LIBRARY_API_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": LIBRARY_SYNC_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            print("Sync erfolgreich:", resp.read().decode())
    except urllib.error.HTTPError as e:
        print("Sync fehlgeschlagen:", e.code, e.read().decode())
        raise


if __name__ == "__main__":
    main()
