import os

from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import package_dir
from pysaurus.core.modules import System
from pysaurus.application import exceptions

try:
    BIN_PATH = AbsolutePath.join(package_dir(), "bin", System.get_identifier()).assert_dir()
    ALIGNMENT_RAPTOR = AbsolutePath.join(
        BIN_PATH, System.get_lib_basename("alignmentRaptor", prefix="")
    ).assert_file()
    RUN_VIDEO_RAPTOR_BATCH = AbsolutePath.join(
        BIN_PATH, System.get_exe_basename("runVideoRaptorBatch")
    ).assert_file()
    RUN_VIDEO_RAPTOR_THUMBNAILS = AbsolutePath.join(
        BIN_PATH, System.get_exe_basename("runVideoRaptorThumbnails")
    ).assert_file()

    __prev_path = os.environ["PATH"]
    __prev_library_path = os.environ.get("LIBRARY_PATH", "")
    __prev_ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["PATH"] = f"{__prev_path}{os.pathsep}{BIN_PATH}"
    os.environ["LIBRARY_PATH"] = f"{__prev_library_path}{os.pathsep}{BIN_PATH}"
    os.environ["LD_LIBRARY_PATH"] = f"{__prev_ld_library_path}{os.pathsep}{BIN_PATH}"
except Exception as exc:
    raise exceptions.CysaurusUnavailable() from exc
