from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import package_dir
from pysaurus.core.modules import System

BIN_PATH = AbsolutePath.join(package_dir(), "bin", System.get_identifier()).assert_dir()
ALIGNMENT_RAPTOR = AbsolutePath.join(
    BIN_PATH, System.get_lib_basename("alignmentRaptor")
).assert_file()
RUN_VIDEO_RAPTOR_BATCH = AbsolutePath.join(
    BIN_PATH, System.get_exe_basename("runVideoRaptorBatch")
).assert_file()
RUN_VIDEO_RAPTOR_THUMBNAILS = AbsolutePath.join(
    BIN_PATH, System.get_exe_basename("runVideoRaptorThumbnails")
).assert_file()
