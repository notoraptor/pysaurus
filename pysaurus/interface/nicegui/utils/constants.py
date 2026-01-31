"""
Constants for NiceGUI interface.
"""

# Group permission levels
GROUP_FORBIDDEN = 0
GROUP_ONLY_MANY = 1  # Only show groups with multiple videos
GROUP_ALL = 2  # Show all groups including singletons


# Field definitions: (name, title, group_permission, is_string)
# group_permission: 0=forbidden, 1=only_many, 2=all
FIELD_DEFINITIONS = [
    ("audio_bit_rate", "Audio bit rate", GROUP_ALL, False),
    ("audio_bits", "Audio bits per sample", GROUP_ALL, False),
    ("audio_codec", "Audio codec", GROUP_ALL, True),
    ("audio_codec_description", "Audio codec description", GROUP_ALL, True),
    ("bit_rate", "Bit rate", GROUP_ONLY_MANY, False),
    ("bit_depth", "Bit depth", GROUP_ALL, False),
    ("container_format", "Container format", GROUP_ALL, True),
    ("date", "Date modified", GROUP_ONLY_MANY, False),
    ("date_entry_modified", "Date entry modified", GROUP_ONLY_MANY, False),
    ("date_entry_opened", "Date entry opened", GROUP_ONLY_MANY, False),
    ("day", "Day", GROUP_ALL, True),
    ("disk", "Disk", GROUP_ALL, True),
    ("extension", "File extension", GROUP_ALL, True),
    ("file_size", "File size (bytes)", GROUP_ONLY_MANY, False),
    ("file_title", "File title", GROUP_ONLY_MANY, True),
    ("filename", "File path", GROUP_ONLY_MANY, True),
    ("frame_rate", "Frame rate", GROUP_ALL, False),
    ("height", "Height", GROUP_ALL, False),
    ("length", "Length", GROUP_ONLY_MANY, False),
    ("move_id", "Moved files", GROUP_ONLY_MANY, False),
    ("sample_rate", "Sample rate", GROUP_ALL, False),
    ("similarity_id", "Similarity", GROUP_ONLY_MANY, False),
    ("title", "Title", GROUP_ONLY_MANY, True),
    ("video_codec", "Video codec", GROUP_ALL, True),
    ("video_codec_description", "Video codec description", GROUP_ALL, True),
    ("width", "Width", GROUP_ALL, False),
    ("year", "Year", GROUP_ALL, False),
]

# Fields allowed for grouping (not forbidden)
GROUPABLE_FIELDS = [
    (name, title, is_string)
    for name, title, perm, is_string in FIELD_DEFINITIONS
    if perm != GROUP_FORBIDDEN
]

# Sortable fields
SORTABLE_FIELDS = [
    (name, title)
    for name, title, perm, is_string in FIELD_DEFINITIONS
]


# Source tree structure for filtering videos
SOURCE_TREE = {
    "unreadable": {"not_found": None, "found": None},
    "readable": {
        "not_found": {"with_thumbnails": None, "without_thumbnails": None},
        "found": {"with_thumbnails": None, "without_thumbnails": None},
    },
}


# Group sorting options
GROUP_SORTING_OPTIONS = [
    ("field", "Field value"),
    ("length", "Field value length"),
    ("count", "Group size"),
]