import os

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.utils import functions

TEST_LIST_FILE_PATH = AbsolutePath(os.path.join(functions.package_dir(), '..', '..', '.local', 'test_folder.log'))
