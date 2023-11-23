FORMATTED_DURATION_TIME_BASE = "COALESCE(NULLIF(duration_time_base, 0), 1)"
SQL_LENGTH = f"(duration * 1.0 / {FORMATTED_DURATION_TIME_BASE})"

GROUPABLE_FIELDS = {
    "audio_bit_rate": ["audio_bit_rate"],
    "audio_bits": ["audio_bits"],
    "audio_codec": ["audio_codec"],
    "audio_codec_description": ["audio_codec_description"],
    "bit_rate": [
        f"IIF(duration = 0, 0, file_size * {FORMATTED_DURATION_TIME_BASE} / duration)"
    ],
    "bit_depth": ["bit_depth"],
    "container_format": ["container_format"],
    "date": ["mtime"],
    "date_entry_modified": ["COALESCE(date_entry_modified, mtime)"],
    "date_entry_opened": ["COALESCE(date_entry_opened, mtime)"],
    "day": ["strftime('%Y-%m-%d', datetime(mtime, 'unixepoch'))"],
    "disk": ["pysaurus_get_disk(filename, driver_id)"],
    "extension": ["pysaurus_get_extension(filename)"],
    "file_size": ["file_size"],
    "file_title": ["pysaurus_get_file_title(filename)"],
    "file_title_numeric": ["file_title_numeric"],  # todo
    "filename": ["filename"],
    "filename_numeric": ["filename_numeric"],  # todo
    "frame_rate": ["(frame_rate_num * 1.0 / COALESCE(NULLIF(frame_rate_den, 0), 1))"],
    "height": ["height"],
    "length": [SQL_LENGTH],
    "move_id": [f"file_size, {SQL_LENGTH}"],
    "sample_rate": ["sample_rate"],
    "similarity_id": ["similarity_id"],
    "size": ["file_size"],
    "size_length": [f"file_size, {SQL_LENGTH}"],
    "title": ["pysaurus_get_title(filename, meta_title)"],
    "title_numeric": ["title_numeric"],  # todo
    "video_codec": ["video_codec"],
    "video_codec_description": ["video_codec_description"],
    "width": ["width"],
    "year": ["strftime('%Y', datetime(mtime, 'unixepoch'))"],
}
