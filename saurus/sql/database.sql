PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS collection (
	collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	version INTEGER NOT NULL DEFAULT -1,
	date_updated DOUBLE,
	-- Try to prevent having more than 1 row.
	CHECK (collection_id = 0)
);
CREATE TABLE IF NOT EXISTS collection_source (
	source TEXT PRIMARY KEY NOT NULL
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
	watched INTEGER NOT NULL DEFAULT 0,
	-- virtual columns
	readable INTEGER GENERATED ALWAYS AS (1 - unreadable) VIRTUAL,
	found INTEGER GENERATED ALWAYS AS (is_file) VIRTUAL,
	not_found INTEGER GENERATED ALWAYS AS (1- is_file) VIRTUAL,
	--
	duration_time_base_not_null INTEGER GENERATED ALWAYS AS (COALESCE(NULLIF(duration_time_base, 0), 1)) VIRTUAL,
	length_seconds DOUBLE GENERATED ALWAYS AS ((duration * 1.0 / duration_time_base_not_null)) VIRTUAL,
	length_microseconds DOUBLE GENERATED ALWAYS AS ((duration * 1000000.0 / duration_time_base_not_null)) VIRTUAL,
	bit_rate DOUBLE GENERATED ALWAYS AS (IIF(duration = 0, 0, file_size * duration_time_base_not_null / duration)) VIRTUAL,
	date_entry_modified_not_null DOUBLE GENERATED ALWAYS AS (COALESCE(date_entry_modified, mtime)) VIRTUAL,
	date_entry_opened_not_null DOUBLE GENERATED ALWAYS AS (COALESCE(date_entry_opened, mtime)) VIRTUAL,
	day TEXT GENERATED ALWAYS AS (strftime('%Y-%m-%d', datetime(mtime, 'unixepoch'))) VIRTUAL,
	year TEXT GENERATED ALWAYS AS (strftime('%Y', datetime(mtime, 'unixepoch'))) VIRTUAL,
	frame_rate DOUBLE GENERATED ALWAYS AS (frame_rate_num * 1.0 / COALESCE(NULLIF(frame_rate_den, 0), 1)) VIRTUAL,
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

CREATE VIEW IF NOT EXISTS video_property_text (video_id, property_text) AS
SELECT v.video_id, GROUP_CONCAT(v.property_value, ';')
FROM video_property_value AS v
JOIN property AS p ON v.property_id = p.property_id
WHERE p.type = 'str'
GROUP BY v.video_id;

CREATE VIRTUAL TABLE IF NOT EXISTS video_text
USING fts5(video_id UNINDEXED, filename, meta_title, properties);
-- Virtual table can use INSERT, UPDATE, DELETE.
-- SELECT video_id FROM video_text WHERE video_text MATCH 'the_text';

----------------------------------------------------------------------------------------
-- Triggers for video_text.
-- Only for video table.
-- Updates related to property and video_property_value tables must be done manually.
-- [details] Updates related to property and video_property_value tables are handled
-- manually in PysaurusCollection.videos_tag_set() for optimal batch performance
-- and complex validation logic. DO NOT add triggers here.
----------------------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS on_video_insert INSERT ON video
BEGIN
    INSERT INTO video_text(video_id, filename, meta_title) VALUES
    (NEW.video_id, NEW.filename, NEW.meta_title);
END;

CREATE TRIGGER IF NOT EXISTS on_video_update_filename UPDATE OF filename ON video
BEGIN
    UPDATE video_text SET filename = NEW.filename WHERE video_id = OLD.video_id;
END;

CREATE TRIGGER IF NOT EXISTS on_video_update_meta_title UPDATE OF meta_title ON video
BEGIN
    UPDATE video_text SET meta_title = NEW.meta_title WHERE video_id = OLD.video_id;
END;

CREATE TRIGGER IF NOT EXISTS on_video_delete DELETE ON video
BEGIN
    DELETE FROM video_text WHERE video_id = OLD.video_id;
END;

----------------------------------------------------------------------------------------
-- Indexes for video table.
-- Columns used for filtering (WHERE clauses).
----------------------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_video_audio_bit_rate ON video(audio_bit_rate);
CREATE INDEX IF NOT EXISTS idx_video_audio_bits ON video(audio_bits);
CREATE INDEX IF NOT EXISTS idx_video_audio_codec ON video(audio_codec);
CREATE INDEX IF NOT EXISTS idx_video_audio_codec_description ON video(audio_codec_description);
CREATE INDEX IF NOT EXISTS idx_video_channels ON video(channels);
CREATE INDEX IF NOT EXISTS idx_video_container_format ON video(container_format);
CREATE INDEX IF NOT EXISTS idx_video_date_entry_modified ON video(date_entry_modified);
CREATE INDEX IF NOT EXISTS idx_video_date_entry_opened ON video(date_entry_opened);
CREATE INDEX IF NOT EXISTS idx_video_device_name ON video(device_name);
CREATE INDEX IF NOT EXISTS idx_video_discarded ON video(discarded);
CREATE INDEX IF NOT EXISTS idx_video_driver_id ON video(driver_id);
CREATE INDEX IF NOT EXISTS idx_video_duration ON video(duration);
CREATE INDEX IF NOT EXISTS idx_video_duration_time_base ON video(duration_time_base);
CREATE INDEX IF NOT EXISTS idx_video_file_size ON video(file_size);
CREATE INDEX IF NOT EXISTS idx_video_frame_rate_den ON video(frame_rate_den);
CREATE INDEX IF NOT EXISTS idx_video_frame_rate_num ON video(frame_rate_num);
CREATE INDEX IF NOT EXISTS idx_video_height ON video(height);
CREATE INDEX IF NOT EXISTS idx_video_is_file ON video(is_file);
CREATE INDEX IF NOT EXISTS idx_video_meta_title ON video(meta_title);
CREATE INDEX IF NOT EXISTS idx_video_mtime ON video(mtime);
CREATE INDEX IF NOT EXISTS idx_video_sample_rate ON video(sample_rate);
CREATE INDEX IF NOT EXISTS idx_video_similarity_id ON video(similarity_id);
CREATE INDEX IF NOT EXISTS idx_video_unreadable ON video(unreadable);
CREATE INDEX IF NOT EXISTS idx_video_video_codec ON video(video_codec);
CREATE INDEX IF NOT EXISTS idx_video_video_codec_description ON video(video_codec_description);
CREATE INDEX IF NOT EXISTS idx_video_watched ON video(watched);
CREATE INDEX IF NOT EXISTS idx_video_width ON video(width);

----------------------------------------------------------------------------------------
-- Indexes for video_property_value table.
-- Used heavily for property lookups and grouping.
----------------------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_vpv_video_id ON video_property_value(video_id);
CREATE INDEX IF NOT EXISTS idx_vpv_property_id ON video_property_value(property_id);
CREATE INDEX IF NOT EXISTS idx_vpv_property_value ON video_property_value(property_id, property_value);
