from typing import Sequence

import videre

from pysaurus.core.absolute_path import AbsolutePath


class PathSetView(videre.Container):
    _background_color = videre.parse_color((128, 128, 128, 32))
    _border = videre.Border.all(1, videre.Colors.lightgray)
    __wprops__ = {}
    __slots__ = ("_paths", "_input", "_message", "_paths_view")

    def __init__(self, paths: Sequence[AbsolutePath] = ()):
        self._paths = set(paths)
        self._input = videre.TextInput(weight=1)
        self._message = videre.Text("", color=videre.Colors.red, strong=True)
        self._paths_view = videre.Column([], space=2)
        super().__init__(
            videre.Column(
                [
                    videre.Container(
                        videre.Text("Path set", strong=True, color=videre.Colors.white),
                        background_color=videre.Colors.black,
                        padding=videre.Div.__style__.default.padding,
                    ),
                    videre.Row(
                        [
                            videre.Button(
                                "Folder ...", on_click=self._on_choose_folder
                            ),
                            videre.Button("Files ...", on_click=self._on_choose_files),
                            videre.Button("File ...", on_click=self._on_choose_file),
                            self._input,
                            videre.Button("add", on_click=self._on_add),
                        ],
                        space=5,
                        vertical_alignment=videre.Alignment.CENTER,
                    ),
                    self._message,
                    videre.Container(
                        videre.ScrollView(
                            videre.Container(
                                self._paths_view, padding=videre.Padding.all(4)
                            )
                        ),
                        border=self._border,
                        weight=1,
                    ),
                ],
                space=5,
            ),
            background_color=None,
            border=self._border,
            padding=videre.Padding.all(10),
        )
        self._update_view()

    def _on_choose_folder(self, *args):
        path = videre.Dialog.select_directory()
        self._input.value = path
        self._add(path)

    def _on_choose_files(self, *args):
        paths = []
        for path_string in videre.Dialog.select_many_files():
            path = AbsolutePath(path_string)
            if path.exists() and path not in self._paths:
                paths.append(path)
        if paths:
            self._paths.update(paths)
            self._message.text = ""
            self._update_view()

    def _on_choose_file(self, *args):
        path = videre.Dialog.select_file_to_open()
        self._input.value = path
        self._add(path)

    def _on_add(self, *args):
        path_string = self._input.value
        self._add(path_string)

    def _add(self, path_string: str):
        if path_string:
            path = AbsolutePath(path_string)
            if not path.exists():
                self._message.text = "This path does not exist"
            else:
                self._message.text = ""
                self._paths.add(path)
                self._update_view()

    def _update_view(self):
        self._paths_view.controls = [
            self._get_path_view(path) for path in self.paths
        ] or [videre.Text("(empty path set)", italic=True)]

    def _get_path_view(self, path: AbsolutePath):
        return videre.Row(
            [
                videre.Button("remove", data=path, on_click=self._on_remove_path),
                videre.Text(str(path)),
            ],
            space=5,
            vertical_alignment=videre.Alignment.CENTER,
        )

    def _on_remove_path(self, widget):
        path: AbsolutePath = widget.data
        self._remove(path)

    def _remove(self, path: AbsolutePath):
        self._message.text = ""
        if path in self._paths:
            self._paths.remove(path)
            self._update_view()

    @property
    def paths(self) -> list[AbsolutePath]:
        return sorted(self._paths)
