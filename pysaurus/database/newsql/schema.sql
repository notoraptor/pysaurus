-- Pysaurus SQL Database Schema
-- Version 1

-- Configuration et métadonnées de la base
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT  -- JSON pour flexibilité
);

-- Dossiers surveillés
CREATE TABLE IF NOT EXISTS folders (
    path TEXT PRIMARY KEY
);

-- Types de propriétés (tags personnalisés)
CREATE TABLE IF NOT EXISTS prop_types (
    name TEXT PRIMARY KEY,
    definition TEXT,  -- JSON: liste des valeurs enum, ou null
    multiple INTEGER NOT NULL DEFAULT 0  -- 0 = single value, 1 = multi-value
);

-- Vidéos (stockage JSON)
CREATE TABLE IF NOT EXISTS videos (
    video_id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE NOT NULL,
    data TEXT NOT NULL  -- JSON complet des métadonnées
);

-- Thumbnails (miniatures)
CREATE TABLE IF NOT EXISTS thumbnails (
    filename TEXT PRIMARY KEY,
    blob BLOB NOT NULL
);

-- Index de recherche: termes textuels
-- Pour les Term (mots du filename, meta_title, valeurs de propriétés)
CREATE TABLE IF NOT EXISTS search_terms (
    term TEXT NOT NULL,
    filename TEXT NOT NULL,
    PRIMARY KEY (term, filename)
);

CREATE INDEX IF NOT EXISTS idx_search_terms_term ON search_terms(term);
CREATE INDEX IF NOT EXISTS idx_search_terms_filename ON search_terms(filename);

-- Index de recherche: flags booléens
-- Pour les Tag (readable, found, discarded, etc.)
CREATE TABLE IF NOT EXISTS video_flags (
    filename TEXT NOT NULL,
    flag TEXT NOT NULL,
    value INTEGER NOT NULL,  -- 0 ou 1
    PRIMARY KEY (filename, flag)
);

CREATE INDEX IF NOT EXISTS idx_video_flags_flag_value ON video_flags(flag, value);