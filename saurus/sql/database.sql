PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS application (
	application_id INTEGER PRIMARY KEY AUTOINCREMENT,
	lang TEXT NOT NULL DEFAULT "english",
	UNIQUE (application_id),
	CHECK (application_id = 0)
);

CREATE TABLE IF NOT EXISTS collection (
	collection_id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	version INTEGER NOT NULL DEFAULT -1,
	date_updated DOUBLE NOT NULL,
	miniature_pixel_distance_radius INTEGER NOT NULL DEFAULT 6,
	miniature_group_min_size INTEGER NOT NULL DEFAULT 0,
	UNIQUE (name)
);
CREATE TABLE IF NOT EXISTS collection_source (
	collection_id INTEGER REFERENCES collection(collection_id) ON DELETE CASCADE,
	source TEXT NOT NULL,
	UNIQUE (collection_id, source)
);

CREATE TABLE IF NOT EXISTS video (
	-- 24 fields
	video_id INTEGER PRIMARY KEY AUTOINCREMENT,
	filename TEXT NOT NULL,
	file_size INTEGER NOT NULL DEFAULT 0,
	mtime DOUBLE NOT NULL DEFAULT 0.0,
	driver_id INTEGER NOT NULL DEFAULT 0,
	is_file INTEGER NOT NULL DEFAULT 0,
	readable INTEGER NOT NULL DEFAULT 0,
	audio_bit_rate INTEGER NOT NULL DEFAULT 0,
	audio_codec TEXT NOT NULL DEFAULT "",
	audio_codec_description TEXT NOT NULL DEFAULT "",
	bit_depth INTEGER NOT NULL DEFAULT 0,
	channels INTEGER NOT NULL DEFAULT 2,
	container_format TEXT NOT NULL DEFAULT "",
	device_name TEXT NOT NULL DEFAULT "",
	duration INTEGER NOT NULL DEFAULT 0,
	duration_time_base INTEGER NOT NULL DEFAULT 0,
	frame_rate_den INTEGER NOT NULL DEFAULT 0,
	frame_rate_num INTEGER NOT NULL DEFAULT 0,
	height INTEGER NOT NULL DEFAULT 0,
	meta_title TEXT NOT NULL DEFAULT "",
	sample_rate INTEGER NOT NULL DEFAULT 0,
	video_codec TEXT NOT NULL DEFAULT "",
	video_codec_description TEXT NOT NULL DEFAULT "",
	width INTEGER NOT NULL DEFAULT 0,
	CHECK (is_file IN (0, 1)),
	CHECK (readable IN (0, 1)),
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
	CHECK (stream IN ("audio", "subtitle")),
	CHECK (rank >= 0),
	UNIQUE (video_id, stream, lang_code, rank)
);

CREATE TABLE IF NOT EXISTS property (
	property_id INTEGER PRIMARY KEY AUTOINCREMENT,
	collection_id INTEGER REFERENCES collection(collection_id) ON DELETE CASCADE,
	name TEXT NOT NULL,
	type TEXT NOT NULL,
	-- default IS NULL => multiple property, else => unique property
	default_value TEXT,
	CHECK (type IN ("bool", "int", "float", "str")),
	UNIQUE (collection_id, name)
);
CREATE TABLE IF NOT EXISTS property_enumeration (
	property_id INTEGER REFERENCES property(property_id) ON DELETE CASCADE,
	enum_value TEXT NOT NULL,
	rank INTEGER NOT NULL,
	CHECK (rank >= 0),
	UNIQUE (property_id, enum_value),
	UNIQUE (property_id, rank)
);

CREATE TABLE IF NOT EXISTS collection_to_video (
	collection_id INTEGER REFERENCES collection(collection_id) ON DELETE CASCADE,
	video_id INTEGER REFERENCES video(video_id) ON DELETE CASCADE,
	thumb_name TEXT NOT NULL DEFAULT "",
	similarity_id INTEGER,
	UNIQUE (collection_id, video_id),
	UNIQUE (collection_id, thumb_name)
);
CREATE TABLE IF NOT EXISTS video_property_value (
	video_id INTEGER REFERENCES video(video_id) ON DELETE CASCADE,
	property_id INTEGER REFERENCES property(property_id) ON DELETE CASCADE,
	property_value TEXT,
	UNIQUE (video_id, property_id, property_value)
);

INSERT OR IGNORE INTO application (application_id) VALUES (0);
