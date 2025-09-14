UNDEFINED = object()
VIDEO_BATCH_SIZE = 250
PYTHON_ERROR_THUMBNAIL = "PYTHON_ERROR_THUMBNAIL"
THUMBNAIL_EXTENSION = "png"
JPEG_EXTENSION = "jpg"
VIDEO_SUPPORTED_EXTENSIONS = frozenset(
    (
        # "!qB".lower(),  # qbittorrent incomplete downloads. TODO Should not be parsed
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
        "mts",
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
assert len(VIDEO_SUPPORTED_EXTENSIONS) == 40, (
    len(VIDEO_SUPPORTED_EXTENSIONS),
    VIDEO_SUPPORTED_EXTENSIONS,
)
PAGE_SIZES = [1, 10, 20, 50, 100]
VIDEO_DEFAULT_PAGE_SIZE = PAGE_SIZES[-1]
VIDEO_DEFAULT_PAGE_NUMBER = 0
VIDEO_DEFAULT_SORTING = ["-date"]
PYTHON_DEFAULT_SOURCES = [["readable"]]
