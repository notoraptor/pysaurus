import pygame

from videre.utils.pygame_font_factory import FONT_FACTORY
from videre.widgets.widget import Widget


class Text(Widget):
    __attributes__ = {"text", "size", "wrap"}
    __slots__ = ()

    def __init__(self, text="", size=0, wrap=True, **kwargs):
        super().__init__(**kwargs)
        self._set_attribute("text", text)
        self._set_attribute("size", size)
        self._set_attribute("wrap", wrap)

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
        return FONT_FACTORY.render_wrap_chars_0(
            self.text, width if self.wrap else None, self.size
        )
