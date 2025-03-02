import chardet
import pygame

SCRAP_UNICODE = "text/plain;charset=utf-8"

_TEXT_TYPES = [SCRAP_UNICODE, pygame.SCRAP_TEXT]


def bytes_to_text(data: bytes) -> str:
    # Try encodings
    for enc in ["utf-32", "utf-16", "utf-8", "ISO-8859-1"]:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    else:
        # Try chardet
        detection = chardet.detect(data)
        encoding = detection["encoding"]
        if encoding:
            return data.decode(encoding)
    # By default, return empty string
    return ""


class Clipboard:
    __slots__ = ()

    @classmethod
    def _get_text_type(cls) -> str:
        for ct in pygame.scrap.get_types():
            if ct == "text/plain;charset=utf-8":
                return ct
        else:
            return pygame.SCRAP_TEXT

    @classmethod
    def get_clipboard(cls) -> str:
        for text_type in _TEXT_TYPES:
            data = pygame.scrap.get(text_type)
            if data:
                data = bytes_to_text(data)
            if data:
                return data
        return ""

    @classmethod
    def set_clipboard(cls, text: str):
        pygame.scrap.put(cls._get_text_type(), text.encode())
