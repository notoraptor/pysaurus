import pygame

from other.pyguisaurus.pygame_font_factory import PygameFontFactory
from other.pyguisaurus.widget import Widget


class Text(Widget):
    __attributes__ = {"text", "size", "wrap"}
    __slots__ = ()
    _FONT_FACTORY = PygameFontFactory()

    def __init__(self, text="", size=0, wrap=True, **kwargs):
        super().__init__(**kwargs)
        self._set_attribute("text", text)
        self._set_attribute("size", size)
        self._set_attribute("wrap", wrap)

    @classmethod
    def lorem_ipsum(cls) -> str:
        return cls._FONT_FACTORY.lorem_ipsum()

    @property
    def text(self) -> str:
        return self._get_attribute("text")

    @property
    def size(self) -> int:
        return self._get_attribute("size")

    @property
    def wrap(self) -> bool:
        return self._get_attribute("wrap")

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        return self._FONT_FACTORY.render_wrap_chars_0(
            self.text, width if self.wrap else None, self.size
        )
