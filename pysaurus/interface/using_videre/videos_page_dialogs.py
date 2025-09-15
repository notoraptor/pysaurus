import videre

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.interface.using_videre.path_set_view import PathSetView


class DialogRenameDatabase(videre.Column):
    __wprops__ = {}
    __slots__ = ("_entry",)

    def __init__(self, old_name: str):
        self._entry = videre.TextInput(old_name)
        super().__init__(
            [
                videre.Text("Old name:"),
                videre.Text(old_name),
                videre.Text("New name:"),
                self._entry,
            ],
            horizontal_alignment=videre.Alignment.CENTER,
            expand_horizontal=True,
            space=10,
        )

    def get_value(self) -> str:
        return self._entry.value


class DialogEditDatabaseFolders(videre.Column):
    __wprops__ = {}
    __slots__ = ("_view",)

    def __init__(self, paths: list[AbsolutePath], title=""):
        self._view = PathSetView(paths, title=title, weight=1)
        super().__init__([videre.Text("Edit database folders:"), self._view])

    def get_paths(self) -> list[AbsolutePath]:
        return self._view.paths
