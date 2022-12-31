CREATE TABLE IF NOT EXISTS filename_to_term (
    filename TEXT NOT NULL,
    term TEXT NOT NULL,
    term_rank INTEGER NOT NULL,
    UNIQUE (filename, term, term_rank),
    UNIQUE (filename, term_rank)
);
