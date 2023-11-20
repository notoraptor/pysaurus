GROUPABLE_FIELDS = {
    "audio_bit_rate": ["audio_bit_rate"],
    "audio_bits": ["audio_bits"],
    "audio_codec": ["audio_codec"],
    "audio_codec_description": ["audio_codec_description"],
    "bit_rate": [
        "IIF(duration = 0, 0, file_size * COALESCE(NULLIF(duration_time_base, 0), 1) / duration)"
    ],
    "bit_depth": ["bit_depth"],
    "container_format": ["container_format"],
    "date": ["mtime"],
    "date_entry_modified": ["COALESCE(date_entry_modified, mtime)"],
    "date_entry_opened": ["COALESCE(date_entry_opened, mtime)"],
    "day": ["strftime('%Y-%m-%d', datetime(mtime, 'unixepoch'))"],
    "disk": ["disk"],  # todo
    "extension": ["extension"],  # todo
    "file_size": ["file_size"],
    "file_title": ["file_title"],  # todo
    "file_title_numeric": ["file_title_numeric"],  # todo
    "filename": ["filename"],
    "filename_numeric": ["filename_numeric"],  # todo
    "frame_rate": ["(frame_rate_num * 1.0 / COALESCE(NULLIF(frame_rate_den, 0), 1))"],
    "height": ["height"],
    "length": ["length"],  # todo
    "move_id": ["move_id"],  # todo
    "sample_rate": ["sample_rate"],
    "similarity_id": ["similarity_id"],
    "size": ["size"],  # todo
    "size_length": ["size_length"],  # todo
    "title": ["title"],  # todo
    "title_numeric": ["title_numeric"],  # todo
    "video_codec": ["video_codec"],
    "video_codec_description": ["video_codec_description"],
    "width": ["width"],
    "year": ["strftime('%Y', datetime(mtime, 'unixepoch'))"],
}
