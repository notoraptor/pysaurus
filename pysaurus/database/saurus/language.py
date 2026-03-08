from pysaurus.core import dict_file_format as dff
from pysaurus.core.absolute_path import AbsolutePath, PathType
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.modules import FNV64
from dataclasses import dataclass, field
from filelock import SoftFileLock


@dataclass
class Language:
    default: str = "english"
    current: str = "english"
    folder: PathType | None = None
    data: dict[str, str] = field(default_factory=dict)

    def __str__(self):
        return dff.dff_dumps(self.data)

    def __len__(self):
        return len(self.data)

    def __call__(self, text: str, **placeholders) -> str:
        """Translate."""
        # Update language
        key = self.key_of(text)
        if key not in self.data:
            self.data[key] = text
            self._save_data()
        # return translation
        translation = self.data[key]
        if placeholders:
            translation = translation.format(**placeholders)
        return translation

    def set_internal(self, dictionary: dict):
        dictionary = dictionary or {}
        self.default = dictionary.get("default", self.default)
        self.current = dictionary.get("current", self.current)
        self.folder = dictionary.get("folder", self.folder)
        self.data = dictionary.get("data", self.data)

    def set_folder(self, folder: PathType):
        if folder is None:
            self.folder = None
            self._update_data()
        else:
            folder = str(AbsolutePath.ensure(folder).assert_dir())
            if self.folder is None or self.folder != folder:
                self.folder = folder
                self._update_data()

    def set_language(self, language: str):
        if self.current != language:
            self.current = language
            self._update_data()

    @classmethod
    def key_of(cls, text: str) -> str:
        pieces = string_to_pieces(text)
        if len(pieces) > 20:
            pieces = pieces[:20] + ["..."]
        hl_key = "".join(piece.title() for piece in pieces)
        return f"{hl_key}_{FNV64.hash(text)}"

    def _update_data(self):
        self.data.clear()
        path = self._get_current_path()
        if path and path.isfile():
            with SoftFileLock(f"{path}.lock"):
                self.data = dff.dff_load(path)

    def _save_data(self):
        path = self._get_current_path()
        if path and path.isfile():
            with SoftFileLock(f"{path}.lock"):
                dff.dff_dump(self.data, path)

    def _get_current_path(self) -> AbsolutePath | None:
        return (
            None
            if self.folder is None
            else AbsolutePath.join(self.folder, f"{self.current}.txt")
        )


say = Language()
