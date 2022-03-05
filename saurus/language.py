from typing import Optional

from pysaurus.core import dict_file_format as dff
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.modules import FNV64


class __Language:
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

    def translate(self, text: str) -> str:
        path = self.current_path
        if self.data is None:
            # load language
            if path.isfile():
                self.data = dff.dff_load(self.current_path)
            else:
                self.data = {}
        # Update language
        key = self._key_of(text)
        if key not in self.data:
            self.data[key] = text
            dff.dff_dump(self.data, self.current_path)
        # return translation
        print(key, self.data[key])
        return self.data[key]

    def __call__(self, text: str) -> str:
        return self.translate(text)


say = __Language()
