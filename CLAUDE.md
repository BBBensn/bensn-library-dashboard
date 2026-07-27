---
date_created: 2026-07-27 01:15:26
date_modified: 2026-07-27 00:10:00
---
CLAUDE.md

Projekt-spezifischer Kontext. Ergänzt `~/.claude/CLAUDE.md`.
Ablageort: `~/Documents/Coding/bensn-hub/stream/Library Dashboard/CLAUDE.md`

---

## Projekt-Basics

- **Name:** bensn-library-dashboard
- **Domain:** library.bensn.me (live)
- **Version:** v1.0.0
- **Status:** ✅ live — Wishlist + Bestandsliste deployed
- **Stack:** Flask + PostgreSQL (bestehende bensn-postgres/bensnos-Instanz) + Vanilla JS/HTML,
  Design-System bensn.css/bensn.js

**Hinweis:** Der ursprünglich geplante Metadaten-Editor ist NICHT Teil dieses Projekts —
er gehört zu einer anderen Library/einem anderen, noch nicht bereiten Projekt. Der private
Bereich hier (`/admin`) dient ausschließlich der Wishlist-Status-Verwaltung.

---

## Lokale Struktur
```
Library Dashboard/
├── frontend/
│   ├── index.html          ← öffentlich: Wishlist-Tab + Bestand-Tab
│   └── admin/
│       └── index.html      ← privat (bensn-auth): Wishlist-Status verwalten
├── backend/
│   └── app.py               ← Flask: wishlist + library Endpoints
├── nas/
│   └── sync_library.py      ← läuft auf TrueNAS (Cron), pusht an /api/library/sync
├── db/
│   └── schema.sql            ← wishlist_items + library_items
├── deploy/
│   ├── library-api.service  ← systemd unit
│   └── nginx-library.bensn.me ← Nginx-Vhost
├── docs/
│   └── changelogs/
├── CLAUDE.md
└── .gitignore
```

---

## Remote-Struktur
```
/var/www/library/
├── public/            ← Wishlist + Bestand (Static, öffentlich)
│   └── admin/         ← Wishlist-Status-Verwaltung (privat, bensn-auth)
└── api/
    ├── app.py
    └── .env            ← DATABASE_URL, LIBRARY_SYNC_KEY (chmod 600, www-data)

NAS (TrueNAS, 192.168.0.63):
/mnt/atlas/library-sync/sync_library.py  ← Cron Job, nachts, pusht Bestand an library.bensn.me
```

---

## Services & Ports

| Dienst | Port | systemd-Service |
|--------|------|-----------------|
| library-api | **5006** (5004/5005 waren bereits durch bubenmarket/andere Services belegt) | `library-api.service` |

---

## Deploy

```bash
# Frontend (öffentlich)
scp frontend/index.html bensn:/var/www/library/public/index.html

# Frontend (Admin)
scp frontend/admin/index.html bensn:/var/www/library/public/admin/index.html

# Backend
scp backend/app.py bensn:/var/www/library/api/app.py
ssh bensn systemctl restart library-api

# Nginx-Vhost
scp deploy/nginx-library.bensn.me bensn:/etc/nginx/sites-enabled/library.bensn.me
ssh bensn "nginx -t && systemctl reload nginx"

# DB-Migration (einmalig, bereits erledigt für v1.0.0)
ssh bensn docker exec -i bensn-postgres psql -U bensn -d bensnos < db/schema.sql

# NAS-Sync-Script aktualisieren
scp nas/sync_library.py truenas_admin@192.168.0.63:/mnt/atlas/library-sync/sync_library.py
```

DB-Zugriff läuft über einen dedizierten Postgres-User `library_api` (nur SELECT/INSERT/UPDATE/DELETE
auf `wishlist_items` + `library_items`), nicht über den geteilten `bensn`-User — Credentials liegen
ausschließlich in `/var/www/library/api/.env` auf dem Server (chmod 600, www-data), nicht im Repo.

---

## Git

- **Repo:** `https://github.com/BBBensn/bensn-library-dashboard`
- **Remote:** `git remote add origin git@github.com:BBBensn/bensn-library-dashboard.git`

```bash
git add .
git commit -m "..."
git push origin main
```

---

## Auth

- [x] Auth via `auth.bensn.me` (nginx `auth_request`) — nur für `/admin`-Bereich und
      `PATCH /api/wishlist/<id>/status`
- [x] Wishlist-Hauptseite (`/`), Bestandsliste (`GET /api/library`) und
      `POST /api/wishlist` / `GET /api/wishlist`: öffentlich, bewusst kein Auth
- [x] `POST /api/library/sync` (NAS → Hetzner): öffentlich erreichbar, aber eigener
      `X-API-Key` (`LIBRARY_SYNC_KEY`), geprüft direkt in Flask — kein Nginx-Cookie-Gate,
      da externer Aufrufer (analog zu `POST /api/upload` bei feed-api)

---

## Projekt-spezifische Konventionen

- Zwei-Bereiche-Prinzip auf einer Domain: `/` öffentlich, `/admin` hinter bensn-auth —
  analog zum bestehenden Muster bei feed.bensn.me
- Wishlist ist bewusst ohne Nutzerkonten/Verifizierung gehalten (kleiner, bekannter
  Freundeskreis) — kein Rate-Limiting in v1.0.0, bei Bedarf später nachrüsten
- Bestandsliste: eine flache DB-Tabelle (`library_items`), Serien/Staffeln werden erst
  in `GET /api/library` zur Anzeigezeit aus den Episode-Zeilen gruppiert
- Bestandsliste zeigt bewusst **keine Datei-Pfade** (Privacy, da öffentlich einsehbar) —
  nur Format/Codec/Auflösung/Sprache/Größe
- Sync-Mechanik: `POST /api/library/sync` ersetzt bei jedem Lauf den kompletten
  Tabelleninhalt (DELETE + Bulk-INSERT in einer Transaktion), kein Diff/Upsert
- Jellyseerr/Radarr/Sonarr explizit NICHT Teil dieses Projekts (siehe Roadmap v2.0.0
  als möglicher, aber unabhängiger Ausblick)
- Metadaten-Editor explizit NICHT Teil dieses Projekts (anderes Projekt/andere Library)

---

## Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| v1.0.0 | Wishlist (öffentlich + Admin-Status-Verwaltung) + Bestandsliste (Jellyfin-Sync) | ✅ done |
| v2.0.0 | Optional: Jellyseerr/Radarr/Sonarr als eigenständiges, separates Projekt | idee, unabhängig |

---

## Obsidian-Doku

- Projekt-MD: `03_Projects/Coding PC/bensn-library-dashboard/bensn-library-dashboard.md`
- Changelogs: `03_Projects/Coding PC/bensn-library-dashboard/Changelogs/`
- Changelog-All: `03_Projects/Coding PC/bensn-library-dashboard/bensn-library-dashboard-Changelog-All.md`
