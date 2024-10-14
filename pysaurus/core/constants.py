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
PYTHON_DEFAULT_SOURCES = [["readable"]]

# 2024/06/01
# https://fr.wikipedia.org/wiki/Lorem_ipsum
LOREM_IPSUM = """
« Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus. Suspendisse lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor. Cras elementum ultrices diam. Maecenas ligula massa, varius a, semper congue, euismod non, mi. Proin porttitor, orci nec nonummy molestie, enim est eleifend mi, non fermentum diam nisl sit amet erat. Duis semper. Duis arcu massa, scelerisque vitae, consequat in, pretium a, enim. Pellentesque congue. Ut in risus volutpat libero pharetra tempor. Cras vestibulum bibendum augue. Praesent egestas leo in pede. Praesent blandit odio eu enim. Pellentesque sed dui ut augue blandit sodales. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Aliquam nibh. Mauris ac mauris sed pede pellentesque fermentum. Maecenas adipiscing ante non diam sodales hendrerit.

Ut velit mauris, egestas sed, gravida nec, ornare ut, mi. Aenean ut orci vel massa suscipit pulvinar. Nulla sollicitudin. Fusce varius, ligula non tempus aliquam, nunc turpis ullamcorper nibh, in tempus sapien eros vitae ligula. Pellentesque rhoncus nunc et augue. Integer id felis. Curabitur aliquet pellentesque diam. Integer quis metus vitae elit lobortis egestas. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Morbi vel erat non mauris convallis vehicula. Nulla et sapien. Integer tortor tellus, aliquam faucibus, convallis id, congue eu, quam. Mauris ullamcorper felis vitae erat. Proin feugiat, augue non elementum posuere, metus purus iaculis lectus, et tristique ligula justo vitae magna.

Aliquam convallis sollicitudin purus. Praesent aliquam, enim at fermentum mollis, ligula massa adipiscing nisl, ac euismod nibh nisl eu lectus. Fusce vulputate sem at sapien. Vivamus leo. Aliquam euismod libero eu enim. Nulla nec felis sed leo placerat imperdiet. Aenean suscipit nulla in justo. Suspendisse cursus rutrum augue. Nulla tincidunt tincidunt mi. Curabitur iaculis, lorem vel rhoncus faucibus, felis magna fermentum augue, et ultricies lacus lorem varius purus. Curabitur eu amet. »
""".strip()
