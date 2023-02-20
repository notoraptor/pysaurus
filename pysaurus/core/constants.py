VIDEO_BATCH_SIZE = 250
PYTHON_ERROR_THUMBNAIL = "PYTHON_ERROR_THUMBNAIL"
THUMBNAIL_EXTENSION = "png"
JPEG_EXTENSION = "jpg"
VIDEO_SUPPORTED_EXTENSIONS = frozenset(
    (
        "3g2",
        "3gp",
        "asf",
        "avi",
        "drc",
        "f4a",
        "f4b",
        "f4p",
        "f4v",
        "flv",
        "gifv",
        "m2ts",
        "m2v",
        "m4p",
        "m4v",
        "mkv",
        "mng",
        "mov",
        "mp2",
        "mp4",
        "mpe",
        "mpeg",
        "mpg",
        "mpv",
        "mxf",
        "nsv",
        "ogg",
        "ogv",
        "qt",
        "rm",
        "rmvb",
        "roq",
        "svi",
        "ts",
        "vid",
        "vob",
        "webm",
        "wmv",
        "yuv",
    )
)
assert len(VIDEO_SUPPORTED_EXTENSIONS) == 39, (
    len(VIDEO_SUPPORTED_EXTENSIONS),
    VIDEO_SUPPORTED_EXTENSIONS,
)
