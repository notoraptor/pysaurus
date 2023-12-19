PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS collection (
	collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	version INTEGER NOT NULL DEFAULT -1,
	date_updated DOUBLE,
	miniature_pixel_distance_radius INTEGER NOT NULL DEFAULT 6,
	miniature_group_min_size INTEGER NOT NULL DEFAULT 0,
	-- Try to prevent having more than 1 row.
	UNIQUE (collection_id),
	CHECK (collection_id = 0)
);
CREATE TABLE IF NOT EXISTS collection_source (
	source TEXT NOT NULL,
	UNIQUE (source)
);

CREATE TABLE IF NOT EXISTS video (
	-- 28 fields
	video_id INTEGER PRIMARY KEY AUTOINCREMENT,
	filename TEXT NOT NULL,
	file_size INTEGER NOT NULL DEFAULT 0,
	unreadable INTEGER NOT NULL DEFAULT 0,
	audio_bit_rate INTEGER NOT NULL DEFAULT 0,
	audio_bits INTEGER NOT NULL DEFAULT 0,
	audio_codec TEXT NOT NULL DEFAULT "",
	audio_codec_description TEXT NOT NULL DEFAULT "",
	bit_depth INTEGER NOT NULL DEFAULT 0,
	channels INTEGER NOT NULL DEFAULT 0,
	container_format TEXT NOT NULL DEFAULT "",
	device_name TEXT NOT NULL DEFAULT "",
	duration DOUBLE NOT NULL DEFAULT 0.0,
	duration_time_base INTEGER NOT NULL DEFAULT 0,
	frame_rate_den INTEGER NOT NULL DEFAULT 0,
	frame_rate_num INTEGER NOT NULL DEFAULT 0,
	height INTEGER NOT NULL DEFAULT 0,
	meta_title TEXT NOT NULL DEFAULT "",
	sample_rate INTEGER NOT NULL DEFAULT 0,
	video_codec TEXT NOT NULL DEFAULT "",
	video_codec_description TEXT NOT NULL DEFAULT "",
	width INTEGER NOT NULL DEFAULT 0,
	-- runtime
	mtime DOUBLE NOT NULL DEFAULT 0.0,
	driver_id INTEGER,
	is_file INTEGER NOT NULL DEFAULT 0,
	discarded INTEGER NOT NULL DEFAULT 0,
	-- mutable
	date_entry_modified DOUBLE,
	date_entry_opened DOUBLE,
	similarity_id INTEGER,
	-- constraints
	CHECK (is_file IN (0, 1)),
	CHECK (discarded IN (0, 1)),
	CHECK (unreadable IN (0, 1)),
	UNIQUE (filename)
);
CREATE TABLE IF NOT EXISTS video_error (
	video_id INTEGER REFERENCES video(video_id) ON DELETE CASCADE,
	error TEXT NOT NULL,
	UNIQUE (video_id, error)
);
CREATE TABLE IF NOT EXISTS video_language (
	video_id INTEGER REFERENCES video(video_id) ON DELETE CASCADE,
	stream TEXT NOT NULL,
	lang_code TEXT NOT NULL,
	rank INTEGER NOT NULL,
	CHECK (stream IN ("a", "s")), -- (a)udio, (s)ubtitle
	CHECK (rank >= 0),
	UNIQUE (video_id, stream, lang_code, rank)
);

CREATE TABLE IF NOT EXISTS property (
	property_id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	type TEXT NOT NULL,
	multiple INTEGER NOT NULL DEFAULT 0,
	CHECK (type IN ("bool", "int", "float", "str")),
	CHECK (multiple IN (0, 1)),
	CHECK (property_id NOT IN (-1, -2)), -- reserved for usage in video_text
	UNIQUE (name)
);
CREATE TABLE IF NOT EXISTS property_enumeration (
	-- if one value, not enum, and value is default value.
	-- else, enum, and first value (rank == 0) is default value.
	property_id INTEGER REFERENCES property(property_id) ON DELETE CASCADE,
	enum_value TEXT NOT NULL,
	rank INTEGER NOT NULL,
	CHECK (rank >= 0),
	UNIQUE (property_id, enum_value),
	UNIQUE (property_id, rank)
);

CREATE TABLE IF NOT EXISTS video_property_value (
	video_id INTEGER REFERENCES video(video_id) ON DELETE CASCADE,
	property_id INTEGER REFERENCES property(property_id) ON DELETE CASCADE,
	property_value TEXT,
	UNIQUE (video_id, property_id, property_value)
);

CREATE TABLE IF NOT EXISTS video_thumbnail (
    video_id INTEGER REFERENCES video(video_id) ON DELETE CASCADE,
    thumbnail BLOB NOT NULL,
    UNIQUE (video_id)
);
-- Currently unused. Thumb table is in a separate database.

CREATE VIRTUAL TABLE IF NOT EXISTS video_text USING fts5(video_id, kind, content);
-- Virtual table can use INSERT, UPDATE, DELETE.
-- SELECT video_id FROM video_text WHERE content MATCH 'the_text';

---------------------------
-- Triggers for video_text.
---------------------------

CREATE TRIGGER IF NOT EXISTS on_video_insert INSERT ON video
BEGIN
    INSERT INTO video_text(video_id, kind, content) VALUES
    (NEW.video_id, -1, NEW.filename),
    (NEW.video_id, -2, NEW.meta_title);
END;

CREATE TRIGGER IF NOT EXISTS on_video_update_filename UPDATE OF filename ON video
BEGIN
    UPDATE video_text SET content = NEW.filename WHERE video_id = OLD.video_id AND kind = -1;
END;

CREATE TRIGGER IF NOT EXISTS on_video_update_meta_title UPDATE OF meta_title ON video
BEGIN
    UPDATE video_text SET content = NEW.meta_title WHERE video_id = OLD.video_id AND kind = -2;
END;

CREATE TRIGGER IF NOT EXISTS on_video_delete DELETE ON video
BEGIN
    DELETE FROM video_text WHERE video_id = OLD.video_id;
END;

CREATE TRIGGER IF NOT EXISTS on_property_delete DELETE ON property WHEN OLD.type = 'str'
BEGIN
    DELETE FROM video_text WHERE kind = OLD.property_id;
END;

CREATE TRIGGER IF NOT EXISTS on_video_property_value_insert
INSERT ON video_property_value
WHEN (SELECT property_id FROM property WHERE property_id = NEW.property_id AND type = 'str')
BEGIN
    INSERT INTO video_text (video_id, kind, content)
    VALUES (NEW.video_id, NEW.property_id, NEW.property_value);
END;

CREATE TRIGGER IF NOT EXISTS on_video_property_value_update UPDATE ON video_property_value
BEGIN
    UPDATE video_text
    SET video_id = NEW.video_id, kind = NEW.property_id, content = NEW.property_value
    WHERE video_id = OLD.video_id
    AND kind = OLD.property_id
    AND content = OLD.property_value;
END;

CREATE TRIGGER IF NOT EXISTS on_video_property_value_delete DELETE ON video_property_value
BEGIN
    DELETE FROM video_text
    WHERE video_id = OLD.video_id
    AND kind = OLD.property_id
    AND content = OLD.property_value;
END;
