import os

from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath

TEST_LIST_FILE_PATH = AbsolutePath(
    os.path.join(functions.package_dir(), '..', '..', '.local', '.local', 'test_folder.log'))
