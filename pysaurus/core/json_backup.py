import ujson as json

from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.informer import Information
from pysaurus.core.modules import FileSystem
from pysaurus.core.profiling import Profiler


class JsonBackup:
    __slots__ = ("path", "notifier")

    def __init__(self, path: PathType, notifier):
        self.path = AbsolutePath.ensure(path)
        self.notifier = notifier or Information.notifier()

    def load(self, default=dict):
        data = default()
        if self.path.exists():
            with open(self.path.assert_file().path) as output_file:
                data = json.load(output_file)
        return data

    @Profiler.profile_method("JsonBackup.save")
    def save(self, data):
        prev_path = AbsolutePath.file_path(
            self.path.get_directory(), self.path.title, "prev.json"
        )
        # Remove previous file
        prev_path.delete()
        # Move target file to previous file
        if self.path.isfile():
            FileSystem.rename(self.path.path, prev_path.path)
            assert not self.path.isfile()
            assert prev_path.isfile()
        # Store JSON data to target file
        with open(self.path.path, "w") as output_file:
            json.dump(data, output_file, indent=1)
        # Data saved. Previous file may exist. Target file contains data.
        assert self.path.isfile()
