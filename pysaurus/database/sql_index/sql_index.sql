PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS filename (
    filename_id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    UNIQUE (filename)
);

CREATE TABLE IF NOT EXISTS term (
    term_id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    UNIQUE (term)
);

CREATE TABLE IF NOT EXISTS filename_to_term (
    filename_id INTEGER REFERENCES filename (filename_id) ON DELETE CASCADE,
    term_id INTEGER REFERENCES term(term_id) ON DELETE CASCADE,
    term_rank INTEGER NOT NULL,
    UNIQUE (filename_id, term_id, term_rank),
    UNIQUE (filename_id, term_rank)
);
