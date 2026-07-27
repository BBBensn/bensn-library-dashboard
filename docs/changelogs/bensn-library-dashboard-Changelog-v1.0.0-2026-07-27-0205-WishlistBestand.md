---
date_created: 2026-07-27 02:05:00
type: changelog
tags:
  - project
  - changelog
date_modified: 2026-07-27 02:05:00
---

# v1.0.0 — Wishlist + Bestandsliste (2026-07-27)
- Neues Projekt `library.bensn.me` aufgesetzt: Flask-Backend (`library-api`, Port 5006) + Vanilla-JS-Frontend im bensn-Design-System
- Wishlist: öffentliches Formular (Titel, Typ, Wunsch von, Notiz, Priorität) + öffentliche Liste, Status-Verwaltung (offen/in Bearbeitung/erledigt) im privaten `/admin`-Bereich hinter bensn-auth
- Bestandsliste: öffentliche, automatisch synchronisierte Übersicht über die Jellyfin-Library auf stream.bensn.me (Format, Video-/Audio-Codec, Auflösung, Sprache, Dateigröße) — Filme flach, Serien aufklappbar bis auf Episoden-Ebene, sortierbar (u.a. nach Dateigröße) und durchsuchbar
- Nächtlicher Sync-Mechanismus: Python-Script läuft als Cron-Job direkt auf der NAS, fragt die lokale Jellyfin-API ab und pusht den kompletten Bestand an `POST /api/library/sync` (öffentlich erreichbar, aber durch dedizierten `X-API-Key` geschützt)
- Neue Postgres-Tabellen `wishlist_items` + `library_items`, eigener DB-User `library_api` mit auf diese zwei Tabellen beschränkten Rechten
- Nginx-Vhost mit SSL (Let's Encrypt), asymmetrisches Auth-Modell: `/` und Wishlist-/Bestand-Reads öffentlich, `/admin` + `PATCH /api/wishlist/<id>/status` hinter bensn-auth-Cookie
- Metadaten-Editor bewusst nicht gebaut — gehört zu einem separaten, noch nicht bereiten Projekt/einer anderen Library
- GitHub-Repo unter `BBBensn/bensn-library-dashboard` (nicht `bensn/...` wie ursprünglich im Übergabeprompt notiert)
