import os

WINDOWS_PATH_PREFIX = "\\\\?\\"
VIDEO_BATCH_SIZE = 250
PYTHON_ERROR_THUMBNAIL = "PYTHON_ERROR_THUMBNAIL"
THUMBNAIL_EXTENSION = "png"
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

BYTES = 1
KILO_BYTES = 1024
MEGA_BYTES = KILO_BYTES * KILO_BYTES
GIGA_BYTES = KILO_BYTES * MEGA_BYTES
TERA_BYTES = KILO_BYTES * GIGA_BYTES
SIZE_UNIT_TO_STRING = {
    BYTES: "b",
    KILO_BYTES: "Kb",
    MEGA_BYTES: "Mb",
    GIGA_BYTES: "Gb",
    TERA_BYTES: "Tb",
}
CPU_COUNT = os.cpu_count()
USABLE_CPU_COUNT = max(1, CPU_COUNT - 2)
