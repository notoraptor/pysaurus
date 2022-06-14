from abc import abstractmethod
from typing import Optional

from pysaurus.core import dict_file_format as dff
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.modules import FNV64


class _LanguageData:
    __slots__ = ()

    @abstractmethod
    def load(self) -> dict:
        pass

    @abstractmethod
    def dump(self, data: dict):
        pass


class _FileData(_LanguageData):
    __slots__ = ("path",)

    def __init__(self, path: AbsolutePath):
        self.path = path

    def load(self) -> dict:
        return dff.dff_load(self.path) if self.path.isfile() else {}

    def dump(self, data: dict):
        dff.dff_dump(data, self.path)


class _MemoryData(_LanguageData):
    __slots__ = "data",

    def __init__(self):
        self.data = {}

    def load(self) -> dict:
        return self.data

    def dump(self, data: dict):
        self.data = data


class _Language:
    __slots__ = ("default", "current", "folder", "data")

    def __init__(self):
        self.default = "english"
        self.current = "english"
        self.folder: Optional[AbsolutePath] = None
        self.data = None

    def _key_of(self, text: str) -> str:
        pieces = string_to_pieces(text)
        if len(pieces) > 20:
            pieces = pieces[:20] + ["..."]
        hl_key = "".join(piece.title() for piece in pieces)
        return f"{hl_key}_{FNV64.hash(text)}"

    def _get_data_manager(self):
        return _MemoryData() if self.folder is None else _FileData(self.current_path)

    @property
    def current_path(self):
        return AbsolutePath.join(self.folder, f"{self.current}.txt")

    def set_folder(self, folder: PathType):
        folder = AbsolutePath.ensure_directory(folder)
        if self.folder is None or self.folder != folder:
            self.folder = folder
            self.data = None

    def set_language(self, language: str):
        if self.current != language:
            self.current = language
            self.data = None

    def new(self):
        return _Language()

    def translate(self, text: str) -> str:
        data = self._get_data_manager()
        if self.data is None:
            # load language
            self.data = data.load()
        # Update language
        key = self._key_of(text)
        if key not in self.data:
            self.data[key] = text
            data.dump(self.data)
        # return translation
        return self.data[key]

    def __call__(self, text: str) -> str:
        return self.translate(text)

    def __getitem__(self, item):
        return self._key_of(item)


say = _Language()
