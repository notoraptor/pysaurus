"""
Exploratory tests for SQLite3 FTS5 capabilities from Python.

Tests what actually works with:
- Python-registered SQL functions (create_function)
- FTS5 virtual tables with rowid mapping
- Triggers (INSERT/UPDATE/DELETE) on regular tables that write to FTS5
- AUTOINCREMENT + NEW.video_id inside triggers
"""

import sqlite3

import pytest


def _text_to_fts(text: str) -> str:
    """Simplified version of the real _text_to_fts for testing."""
    if text is None:
        return ""
    # Simple camelCase split simulation: insert spaces before uppercase
    result = []
    for i, ch in enumerate(text):
        if ch.isupper() and i > 0 and text[i - 1].islower():
            result.append(" ")
        result.append(ch.lower())
    return "".join(result)


@pytest.fixture
def conn():
    """Fresh in-memory SQLite connection with FTS5 and a video-like table."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    # Register Python function
    c.create_function("text_to_fts", 1, _text_to_fts, deterministic=True)
    # Create tables
    c.executescript("""
        CREATE TABLE video (
            video_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            meta_title TEXT NOT NULL DEFAULT ''
        );
        CREATE VIRTUAL TABLE video_text
            USING fts5(filename, meta_title, properties);
    """)
    yield c
    c.close()


# =============================================================================
# 1. Python function registered via create_function
# =============================================================================


class TestSqlFunction:
    """Test that a Python function registered via create_function works in SQL."""

    def test_function_in_select(self, conn):
        """Registered function can be called in SELECT."""
        row = conn.execute("SELECT text_to_fts('HelloWorld')").fetchone()
        assert row[0] == "hello world"

    def test_function_in_insert(self, conn):
        """Registered function can be used in INSERT values."""
        conn.execute(
            "INSERT INTO video_text (rowid, filename, meta_title) "
            "VALUES (1, text_to_fts('CamelCase'), text_to_fts('MetaTitle'))"
        )
        row = conn.execute(
            "SELECT filename, meta_title FROM video_text WHERE rowid = 1"
        ).fetchone()
        assert row["filename"] == "camel case"
        assert row["meta_title"] == "meta title"

    def test_function_in_update(self, conn):
        """Registered function can be used in UPDATE."""
        conn.execute(
            "INSERT INTO video_text (rowid, filename, meta_title) "
            "VALUES (1, 'old', 'old')"
        )
        conn.execute(
            "UPDATE video_text SET filename = text_to_fts('NewName') WHERE rowid = 1"
        )
        row = conn.execute(
            "SELECT filename FROM video_text WHERE rowid = 1"
        ).fetchone()
        assert row["filename"] == "new name"

    def test_function_with_none(self, conn):
        """Registered function handles NULL input."""
        row = conn.execute("SELECT text_to_fts(NULL)").fetchone()
        assert row[0] == ""

    def test_function_deterministic(self, conn):
        """Deterministic function returns same result for same input."""
        r1 = conn.execute("SELECT text_to_fts('Test')").fetchone()[0]
        r2 = conn.execute("SELECT text_to_fts('Test')").fetchone()[0]
        assert r1 == r2


# =============================================================================
# 2. INSERT trigger: NEW.video_id with AUTOINCREMENT
# =============================================================================


class TestInsertTrigger:
    """Test INSERT triggers on video table that write to FTS5."""

    def test_after_insert_new_video_id(self, conn):
        """AFTER INSERT trigger can read NEW.video_id (autoincrement)."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (NEW.video_id, NEW.filename, NEW.meta_title);
            END
        """)
        conn.execute(
            "INSERT INTO video (filename, meta_title) VALUES ('file1.mp4', 'Title1')"
        )
        # Check video got an ID
        video = conn.execute("SELECT video_id FROM video").fetchone()
        assert video["video_id"] is not None
        vid = video["video_id"]

        # Check FTS row was created with correct rowid
        fts = conn.execute(
            "SELECT rowid, filename, meta_title FROM video_text WHERE rowid = ?",
            [vid],
        ).fetchone()
        assert fts is not None
        assert fts["rowid"] == vid
        assert fts["filename"] == "file1.mp4"
        assert fts["meta_title"] == "Title1"

    def test_after_insert_multiple_rows(self, conn):
        """AFTER INSERT trigger works for multiple sequential inserts."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (NEW.video_id, NEW.filename, NEW.meta_title);
            END
        """)
        for i in range(5):
            conn.execute(
                "INSERT INTO video (filename, meta_title) VALUES (?, ?)",
                [f"file{i}.mp4", f"Title{i}"],
            )

        video_count = conn.execute("SELECT COUNT(*) FROM video").fetchone()[0]
        fts_count = conn.execute("SELECT COUNT(*) FROM video_text").fetchone()[0]
        assert video_count == 5
        assert fts_count == 5

        # Verify rowid mapping
        for row in conn.execute(
            "SELECT v.video_id, t.rowid, v.filename, t.filename "
            "FROM video v JOIN video_text t ON v.video_id = t.rowid"
        ):
            assert row[0] == row[1]  # video_id == rowid
            assert row[2] == row[3]  # filenames match

    def test_after_insert_with_function(self, conn):
        """AFTER INSERT trigger can call registered Python function."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END
        """)
        conn.execute(
            "INSERT INTO video (filename, meta_title) "
            "VALUES ('MyCamelFile.mp4', 'SomeTitle')"
        )
        vid = conn.execute("SELECT video_id FROM video").fetchone()[0]

        fts = conn.execute(
            "SELECT filename, meta_title FROM video_text WHERE rowid = ?", [vid]
        ).fetchone()
        assert fts["filename"] == "my camel file.mp4"
        assert fts["meta_title"] == "some title"

    def test_after_insert_searchable(self, conn):
        """FTS5 row created by trigger is searchable via MATCH."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END
        """)
        conn.execute(
            "INSERT INTO video (filename, meta_title) "
            "VALUES ('MyCamelFile.mp4', 'SomeTitle')"
        )

        # Search for camelCase-split term
        matches = conn.execute(
            "SELECT rowid FROM video_text WHERE video_text MATCH 'camel*'"
        ).fetchall()
        assert len(matches) == 1

    def test_after_insert_executemany(self, conn):
        """AFTER INSERT trigger works with executemany (batch insert)."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END
        """)
        data = [(f"File{i}Name.mp4", f"Title{i}") for i in range(10)]
        conn.executemany(
            "INSERT INTO video (filename, meta_title) VALUES (?, ?)", data
        )

        video_count = conn.execute("SELECT COUNT(*) FROM video").fetchone()[0]
        fts_count = conn.execute("SELECT COUNT(*) FROM video_text").fetchone()[0]
        assert video_count == 10
        assert fts_count == 10

    def test_before_insert_video_id_is_none(self, conn):
        """BEFORE INSERT trigger: NEW.video_id is NULL for autoincrement."""
        # This documents the known limitation
        conn.execute("""
            CREATE TRIGGER on_video_insert_before BEFORE INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (NEW.video_id, NEW.filename, NEW.meta_title);
            END
        """)
        # BEFORE INSERT: NEW.video_id should be NULL for autoincrement
        # This should either fail or produce unexpected results
        try:
            conn.execute(
                "INSERT INTO video (filename, meta_title) VALUES ('f.mp4', 'T')"
            )
            # If it didn't raise, check what rowid was assigned
            fts = conn.execute(
                "SELECT rowid FROM video_text"
            ).fetchone()
            # Document the actual behavior
            pytest.skip(
                f"BEFORE INSERT didn't fail; FTS rowid = {fts[0] if fts else 'none'}"
            )
        except sqlite3.OperationalError:
            pass  # Expected: can't use NULL as rowid for FTS5


# =============================================================================
# 3. UPDATE triggers
# =============================================================================


class TestUpdateTrigger:
    """Test UPDATE triggers on video table that update FTS5."""

    @pytest.fixture(autouse=True)
    def setup_with_data(self, conn):
        """Set up triggers and seed data."""
        self.conn = conn
        # Insert trigger for seeding
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END
        """)
        # UPDATE triggers
        conn.execute("""
            CREATE TRIGGER on_video_update_filename
            AFTER UPDATE OF filename ON video
            BEGIN
                UPDATE video_text
                SET filename = text_to_fts(NEW.filename)
                WHERE rowid = OLD.video_id;
            END
        """)
        conn.execute("""
            CREATE TRIGGER on_video_update_meta_title
            AFTER UPDATE OF meta_title ON video
            BEGIN
                UPDATE video_text
                SET meta_title = text_to_fts(NEW.meta_title)
                WHERE rowid = OLD.video_id;
            END
        """)
        # Seed data
        conn.execute(
            "INSERT INTO video (filename, meta_title) "
            "VALUES ('OriginalFile.mp4', 'OriginalTitle')"
        )
        self.vid = conn.execute("SELECT video_id FROM video").fetchone()[0]

    def test_update_filename_updates_fts(self):
        """UPDATE video SET filename triggers FTS update."""
        self.conn.execute(
            "UPDATE video SET filename = 'RenamedFile.mp4' WHERE video_id = ?",
            [self.vid],
        )
        fts = self.conn.execute(
            "SELECT filename FROM video_text WHERE rowid = ?", [self.vid]
        ).fetchone()
        assert fts["filename"] == "renamed file.mp4"

    def test_update_meta_title_updates_fts(self):
        """UPDATE video SET meta_title triggers FTS update."""
        self.conn.execute(
            "UPDATE video SET meta_title = 'NewMetaTitle' WHERE video_id = ?",
            [self.vid],
        )
        fts = self.conn.execute(
            "SELECT meta_title FROM video_text WHERE rowid = ?", [self.vid]
        ).fetchone()
        assert fts["meta_title"] == "new meta title"

    def test_update_filename_old_not_searchable(self):
        """After UPDATE, old filename must not be found via FTS MATCH."""
        self.conn.execute(
            "UPDATE video SET filename = 'CompletelyDifferent.mp4' WHERE video_id = ?",
            [self.vid],
        )
        matches = self.conn.execute(
            "SELECT rowid FROM video_text WHERE video_text MATCH 'original*'"
        ).fetchall()
        # "original" should only be in meta_title now, not filename
        # Actually "OriginalTitle" is still in meta_title, so we check filename column
        fts = self.conn.execute(
            "SELECT filename FROM video_text WHERE rowid = ?", [self.vid]
        ).fetchone()
        assert "original" not in fts["filename"]

    def test_update_filename_new_searchable(self):
        """After UPDATE, new filename must be found via FTS MATCH."""
        self.conn.execute(
            "UPDATE video SET filename = 'UniqueXyzName.mp4' WHERE video_id = ?",
            [self.vid],
        )
        matches = self.conn.execute(
            "SELECT rowid FROM video_text WHERE video_text MATCH 'xyz*'"
        ).fetchall()
        assert len(matches) == 1
        assert matches[0][0] == self.vid

    def test_update_unrelated_column_no_trigger(self):
        """UPDATE of a column NOT in trigger should not change FTS."""
        fts_before = self.conn.execute(
            "SELECT filename, meta_title FROM video_text WHERE rowid = ?", [self.vid]
        ).fetchone()

        # Update a column that has no trigger (meta_title trigger is for meta_title only)
        # Add a dummy column first
        self.conn.execute("ALTER TABLE video ADD COLUMN watched INTEGER DEFAULT 0")
        self.conn.execute(
            "UPDATE video SET watched = 1 WHERE video_id = ?", [self.vid]
        )

        fts_after = self.conn.execute(
            "SELECT filename, meta_title FROM video_text WHERE rowid = ?", [self.vid]
        ).fetchone()
        assert fts_before["filename"] == fts_after["filename"]
        assert fts_before["meta_title"] == fts_after["meta_title"]

    def test_update_both_columns(self):
        """UPDATE both filename and meta_title in one statement."""
        self.conn.execute(
            "UPDATE video SET filename = 'NewFile.mp4', meta_title = 'NewTitle' "
            "WHERE video_id = ?",
            [self.vid],
        )
        fts = self.conn.execute(
            "SELECT filename, meta_title FROM video_text WHERE rowid = ?", [self.vid]
        ).fetchone()
        assert fts["filename"] == "new file.mp4"
        assert fts["meta_title"] == "new title"

    def test_update_batch(self):
        """Batch UPDATE via executemany triggers FTS updates."""
        # Insert more videos
        for i in range(5):
            self.conn.execute(
                "INSERT INTO video (filename, meta_title) VALUES (?, ?)",
                [f"Batch{i}File.mp4", f"Batch{i}Title"],
            )
        ids = [
            r[0] for r in self.conn.execute("SELECT video_id FROM video").fetchall()
        ]

        # Batch update
        self.conn.executemany(
            "UPDATE video SET meta_title = ? WHERE video_id = ?",
            [(f"Updated{i}Title", vid) for i, vid in enumerate(ids)],
        )

        for i, vid in enumerate(ids):
            fts = self.conn.execute(
                "SELECT meta_title FROM video_text WHERE rowid = ?", [vid]
            ).fetchone()
            assert fts["meta_title"] == _text_to_fts(f"Updated{i}Title")


# =============================================================================
# 4. DELETE trigger
# =============================================================================


class TestDeleteTrigger:
    """Test DELETE trigger on video table removes FTS5 row."""

    def test_delete_removes_fts_row(self, conn):
        """DELETE FROM video must remove the video_text row via trigger."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (NEW.video_id, NEW.filename, NEW.meta_title);
            END
        """)
        conn.execute("""
            CREATE TRIGGER on_video_delete AFTER DELETE ON video
            BEGIN
                DELETE FROM video_text WHERE rowid = OLD.video_id;
            END
        """)
        conn.execute("INSERT INTO video (filename) VALUES ('test.mp4')")
        vid = conn.execute("SELECT video_id FROM video").fetchone()[0]
        assert conn.execute(
            "SELECT COUNT(*) FROM video_text WHERE rowid = ?", [vid]
        ).fetchone()[0] == 1

        conn.execute("DELETE FROM video WHERE video_id = ?", [vid])

        assert conn.execute(
            "SELECT COUNT(*) FROM video_text WHERE rowid = ?", [vid]
        ).fetchone()[0] == 0


# =============================================================================
# 5. Full integration: all triggers + function
# =============================================================================


class TestFullIntegration:
    """Test all triggers together with the registered function."""

    @pytest.fixture(autouse=True)
    def setup_full(self, conn):
        self.conn = conn
        conn.executescript("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END;

            CREATE TRIGGER on_video_update_filename
            AFTER UPDATE OF filename ON video
            BEGIN
                UPDATE video_text
                SET filename = text_to_fts(NEW.filename)
                WHERE rowid = OLD.video_id;
            END;

            CREATE TRIGGER on_video_update_meta_title
            AFTER UPDATE OF meta_title ON video
            BEGIN
                UPDATE video_text
                SET meta_title = text_to_fts(NEW.meta_title)
                WHERE rowid = OLD.video_id;
            END;

            CREATE TRIGGER on_video_delete AFTER DELETE ON video
            BEGIN
                DELETE FROM video_text WHERE rowid = OLD.video_id;
            END;
        """)

    def test_full_lifecycle(self):
        """INSERT -> UPDATE -> DELETE lifecycle with FTS5."""
        # INSERT
        self.conn.execute(
            "INSERT INTO video (filename, meta_title) "
            "VALUES ('MyTestFile.mp4', 'CamelCaseTitle')"
        )
        vid = self.conn.execute("SELECT video_id FROM video").fetchone()[0]

        fts = self.conn.execute(
            "SELECT filename, meta_title FROM video_text WHERE rowid = ?", [vid]
        ).fetchone()
        assert fts["filename"] == "my test file.mp4"
        assert fts["meta_title"] == "camel case title"

        # UPDATE filename
        self.conn.execute(
            "UPDATE video SET filename = 'RenamedCamelFile.mp4' WHERE video_id = ?",
            [vid],
        )
        fts = self.conn.execute(
            "SELECT filename FROM video_text WHERE rowid = ?", [vid]
        ).fetchone()
        assert fts["filename"] == "renamed camel file.mp4"

        # UPDATE meta_title
        self.conn.execute(
            "UPDATE video SET meta_title = 'NewMetaTitle' WHERE video_id = ?",
            [vid],
        )
        fts = self.conn.execute(
            "SELECT meta_title FROM video_text WHERE rowid = ?", [vid]
        ).fetchone()
        assert fts["meta_title"] == "new meta title"

        # DELETE
        self.conn.execute("DELETE FROM video WHERE video_id = ?", [vid])
        assert (
            self.conn.execute(
                "SELECT COUNT(*) FROM video_text WHERE rowid = ?", [vid]
            ).fetchone()[0]
            == 0
        )

    def test_fts_count_always_matches_video_count(self):
        """FTS row count must always match video count."""
        for i in range(10):
            self.conn.execute(
                "INSERT INTO video (filename, meta_title) VALUES (?, ?)",
                [f"File{i}.mp4", f"Title{i}"],
            )
        assert self._video_count() == 10
        assert self._fts_count() == 10

        # Delete some
        self.conn.execute("DELETE FROM video WHERE video_id <= 3")
        assert self._video_count() == self._fts_count()

        # Update remaining
        self.conn.execute("UPDATE video SET filename = 'Same.mp4'")
        assert self._video_count() == self._fts_count()

    def test_search_after_full_lifecycle(self):
        """Search works correctly after insert, update, delete."""
        self.conn.execute(
            "INSERT INTO video (filename, meta_title) "
            "VALUES ('AlphaFile.mp4', 'BetaTitle')"
        )
        self.conn.execute(
            "INSERT INTO video (filename, meta_title) "
            "VALUES ('GammaFile.mp4', 'DeltaTitle')"
        )

        # Search for alpha
        matches = self._match("alpha*")
        assert len(matches) == 1

        # Update first file
        vid1 = self.conn.execute(
            "SELECT video_id FROM video WHERE filename = 'AlphaFile.mp4'"
        ).fetchone()[0]
        self.conn.execute(
            "UPDATE video SET filename = 'EpsilonFile.mp4' WHERE video_id = ?",
            [vid1],
        )

        # Alpha gone, epsilon found
        assert len(self._match("alpha*")) == 0
        assert len(self._match("epsilon*")) == 1

        # Delete second
        vid2 = self.conn.execute(
            "SELECT video_id FROM video WHERE filename = 'GammaFile.mp4'"
        ).fetchone()[0]
        self.conn.execute("DELETE FROM video WHERE video_id = ?", [vid2])
        assert len(self._match("gamma*")) == 0

    def _video_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM video").fetchone()[0]

    def _fts_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM video_text").fetchone()[0]

    def _match(self, expr):
        return self.conn.execute(
            "SELECT rowid FROM video_text WHERE video_text MATCH ?", [expr]
        ).fetchall()


# =============================================================================
# 6. Edge cases and limitations
# =============================================================================


class TestEdgeCases:
    """Test edge cases that might cause problems."""

    def test_trigger_with_function_in_executescript(self, conn):
        """Triggers using registered functions work when created via executescript."""
        # executescript uses a separate internal connection in some implementations
        # Test that the function is available
        conn.executescript("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END;
        """)
        conn.execute("INSERT INTO video (filename) VALUES ('TestFile.mp4')")
        fts = conn.execute("SELECT filename FROM video_text").fetchone()
        assert fts["filename"] == "test file.mp4"

    def test_function_survives_across_transactions(self, conn):
        """Registered function works across multiple transactions."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END
        """)
        conn.execute("BEGIN")
        conn.execute("INSERT INTO video (filename) VALUES ('First.mp4')")
        conn.execute("COMMIT")

        conn.execute("BEGIN")
        conn.execute("INSERT INTO video (filename) VALUES ('Second.mp4')")
        conn.execute("COMMIT")

        assert conn.execute("SELECT COUNT(*) FROM video_text").fetchone()[0] == 2

    def test_trigger_after_drop_and_recreate_fts(self, conn):
        """Triggers still work after dropping and recreating FTS table."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END
        """)
        conn.execute("INSERT INTO video (filename) VALUES ('Before.mp4')")
        assert conn.execute("SELECT COUNT(*) FROM video_text").fetchone()[0] == 1

        # Drop and recreate FTS (simulating repair_fts)
        conn.execute("DROP TRIGGER on_video_insert")
        conn.execute("DROP TABLE video_text")
        conn.execute(
            "CREATE VIRTUAL TABLE video_text "
            "USING fts5(filename, meta_title, properties)"
        )
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END
        """)

        conn.execute("INSERT INTO video (filename) VALUES ('After.mp4')")
        assert conn.execute("SELECT COUNT(*) FROM video_text").fetchone()[0] == 1

    def test_update_trigger_of_clause_specificity(self, conn):
        """UPDATE OF filename trigger does NOT fire on meta_title update."""
        conn.execute(
            "INSERT INTO video (filename, meta_title) VALUES ('f.mp4', 'title')"
        )
        vid = conn.execute("SELECT video_id FROM video").fetchone()[0]
        conn.execute(
            "INSERT INTO video_text (rowid, filename, meta_title) "
            "VALUES (?, 'original_fn', 'original_mt')",
            [vid],
        )

        # Create ONLY filename trigger
        conn.execute("""
            CREATE TRIGGER on_video_update_filename
            AFTER UPDATE OF filename ON video
            BEGIN
                UPDATE video_text
                SET filename = text_to_fts(NEW.filename)
                WHERE rowid = OLD.video_id;
            END
        """)

        # Update meta_title (should NOT trigger filename update)
        conn.execute(
            "UPDATE video SET meta_title = 'changed' WHERE video_id = ?", [vid]
        )
        fts = conn.execute(
            "SELECT filename FROM video_text WHERE rowid = ?", [vid]
        ).fetchone()
        assert fts["filename"] == "original_fn"  # unchanged

    def test_insert_trigger_with_skullite_modify_many(self, conn):
        """Trigger works with parameterized executemany (like Skullite.modify_many)."""
        conn.execute("""
            CREATE TRIGGER on_video_insert AFTER INSERT ON video
            BEGIN
                INSERT INTO video_text (rowid, filename, meta_title)
                VALUES (
                    NEW.video_id,
                    text_to_fts(NEW.filename),
                    text_to_fts(NEW.meta_title)
                );
            END
        """)
        data = [
            {"filename": f"CamelFile{i}.mp4", "meta_title": f"CamelTitle{i}"}
            for i in range(5)
        ]
        conn.executemany(
            "INSERT INTO video (filename, meta_title) "
            "VALUES (:filename, :meta_title)",
            data,
        )
        assert conn.execute("SELECT COUNT(*) FROM video_text").fetchone()[0] == 5

        # Verify all have processed text
        for row in conn.execute("SELECT filename FROM video_text").fetchall():
            assert row["filename"].islower() or " " in row["filename"]
