from pysaurus.core import dict_file_format as dff
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.modules import FNV64


class Language:
    __slots__ = ("dictionary",)
    K_DEFAULT = "default"
    K_CURRENT = "current"
    K_FOLDER = "folder"
    K_DATA = "data"

    def __init__(self, *, folder=None, dictionary=None):
        if dictionary is None:
            dictionary = {}
        self.dictionary = dictionary
        self.dictionary[self.K_DEFAULT] = "english"
        self.dictionary[self.K_CURRENT] = "english"
        self.dictionary[self.K_FOLDER] = None
        self.dictionary[self.K_DATA] = {}
        if folder is not None:
            self.set_folder(folder)

    default = property(lambda self: self.dictionary[self.K_DEFAULT])

    def __str__(self):
        return dff.dff_dumps(self.dictionary[self.K_DATA])

    def __len__(self):
        return len(self.dictionary[self.K_DATA])

    def __call__(self, text: str, **placeholders) -> str:
        """Translate."""
        # Update language
        key = self.key_of(text)
        if key not in self.dictionary[self.K_DATA]:
            tmp_d = self.dictionary[self.K_DATA]
            tmp_d[key] = text
            self.dictionary[self.K_DATA] = tmp_d
            self._save_data()
        # return translation
        translation = self.dictionary[self.K_DATA][key]
        if placeholders:
            translation = translation.format(**placeholders)
        return translation

    def set_internal(self, dictionary: dict):
        assert dictionary is not None
        dictionary.update(self.dictionary)
        self.dictionary = dictionary

    def set_folder(self, folder: PathType):
        if folder is None:
            self.dictionary[self.K_FOLDER] = None
            self._update_data()
        else:
            folder = str(AbsolutePath.ensure_directory(folder))
            if (
                self.dictionary[self.K_FOLDER] is None
                or self.dictionary[self.K_FOLDER] != folder
            ):
                self.dictionary[self.K_FOLDER] = folder
                self._update_data()

    def set_language(self, language: str):
        if self.dictionary[self.K_CURRENT] != language:
            self.dictionary[self.K_CURRENT] = language
            self._update_data()

    @classmethod
    def key_of(cls, text: str) -> str:
        pieces = string_to_pieces(text)
        if len(pieces) > 20:
            pieces = pieces[:20] + ["..."]
        hl_key = "".join(piece.title() for piece in pieces)
        return f"{hl_key}_{FNV64.hash(text)}"

    @property
    def current_path(self):
        return AbsolutePath.join(
            self.dictionary[self.K_FOLDER], f"{self.dictionary[self.K_CURRENT]}.txt"
        )

    def _update_data(self):
        self.dictionary[self.K_DATA].clear()
        if self.dictionary[self.K_FOLDER] is not None:
            path = self.current_path
            if path.isfile():
                self.dictionary[self.K_DATA] = dff.dff_load(path)

    def _save_data(self):
        if self.dictionary[self.K_FOLDER] is not None:
            path = self.current_path
            if path.isfile():
                dff.dff_dump(self.dictionary[self.K_DATA], path)


say = Language()
