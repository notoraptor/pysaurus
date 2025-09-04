from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.absolute_path import AbsolutePath, PathType
from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.interface.common.qt_utils import Callback
from pysaurus.interface.qtsaurus.qts_elided_label import QtsElidedLabel

NAME_FILTER = (
    f"Videos ({' '.join(f'*.{ext}' for ext in sorted(VIDEO_SUPPORTED_EXTENSIONS))})"
)


class QtsPathInput(QWidget):
    def __init__(self, paths: list[PathType] = ()):
        super().__init__()
        self.__paths = sorted(AbsolutePath.ensure(path) for path in paths)

        self.__button_add_file = QPushButton("add file")
        self.__button_add_dir = QPushButton("add folder")
        self.__buttons = QGridLayout()
        self.__labels = QGridLayout()
        self.__layout = QVBoxLayout()
        self.__children = []

        self.__button_add_file.clicked.connect(self._add_file)
        self.__button_add_dir.clicked.connect(self._add_folder)

        self.__buttons.setSizeConstraint(QGridLayout.SizeConstraint.SetMinAndMaxSize)
        self.__labels.setSizeConstraint(QGridLayout.SizeConstraint.SetMinAndMaxSize)
        self.__layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinAndMaxSize)

        self.__buttons.addWidget(self.__button_add_file, 0, 0)
        self.__buttons.addWidget(self.__button_add_dir, 0, 1)
        self.__layout.addLayout(self.__buttons)
        self.__layout.addLayout(self.__labels)
        self.setLayout(self.__layout)

        self.__draw()

    def paths(self) -> list[AbsolutePath]:
        return self.__paths

    def _add_file(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter(NAME_FILTER)
        print(NAME_FILTER)
        if dialog.exec():
            (path,) = dialog.selectedFiles()
            self.__paths = sorted(set(self.__paths) | {AbsolutePath(path)})
            self.__draw()

    def _add_folder(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec():
            (directory,) = dialog.selectedFiles()
            self.__paths = sorted(set(self.__paths) | {AbsolutePath(directory)})
            self.__draw()

    def _delete_path(self, path: AbsolutePath):
        self.__paths = sorted(set(self.__paths) - {path})
        self.__draw()

    def __draw(self):
        for child in self.__children:
            self.__labels.removeWidget(child)
        self.__children.clear()
        for i, path in enumerate(self.__paths):
            label = QtsElidedLabel(path.standard_path)
            button = QPushButton("-")
            button.clicked.connect(Callback(self._delete_path, path))
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.__labels.addWidget(label, i, 0)
            self.__labels.addWidget(button, i, 1)
            self.__children.append(label)
            self.__children.append(button)
