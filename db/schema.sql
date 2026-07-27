-- Library Dashboard v1.0.0
-- Ausfuehren via: docker exec bensn-postgres psql -U bensn -d bensnos -f schema.sql

CREATE TABLE IF NOT EXISTS wishlist_items (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT,                          -- 'movie' | 'series'
    requested_by TEXT,
    note TEXT,
    priority TEXT DEFAULT 'low',        -- 'low' | 'medium' | 'high'
    status TEXT DEFAULT 'open',         -- 'open' | 'in_progress' | 'done'
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS library_items (
    id SERIAL PRIMARY KEY,
    jellyfin_id TEXT UNIQUE NOT NULL,
    item_type TEXT NOT NULL,            -- 'movie' | 'episode'
    title TEXT NOT NULL,
    series_title TEXT,
    series_jellyfin_id TEXT,
    season_number INT,
    episode_number INT,
    year INT,
    container TEXT,
    video_codec TEXT,
    audio_codec TEXT,
    audio_languages TEXT,
    resolution TEXT,
    file_size_bytes BIGINT,
    synced_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_library_items_series ON library_items (series_jellyfin_id);
