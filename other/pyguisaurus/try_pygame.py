import inspect
import logging
import pprint
from abc import abstractmethod
from typing import Any, List, Optional

import pygame
import pygame.freetype
from pygame.event import Event

from other.pyguisaurus.pygame_font_factory import PygameFontFactory


def on_event(event_type: int):
    def decorator(function):
        function.event_type = event_type
        return function

    return decorator


class Widget:
    __attributes__ = ()

    __slots__ = ("_key", "_old", "_new", "_surface", "_old_update")

    def __init__(self, key=None):
        self._key = key or id(self)
        self._old = {}
        self._new = {}
        self._old_update = ()
        self._surface: Optional[pygame.Surface] = None

    def _debug(self, *args, **kwargs):
        print(f"[{type(self).__name__}][{self._key}]", *args, **kwargs)

    @classmethod
    def _has_attribute(cls, name: str) -> bool:
        for typ in cls.__mro__:
            attrs = getattr(typ, "__attributes__", ())
            if name in attrs:
                return True
        return False

    @classmethod
    def _assert_attribute(cls, name):
        assert cls._has_attribute(
            name
        ), f"{cls.__name__}: unknown widget attribute: {name}"

    def _set_attribute(self, name: str, value: Any):
        self._assert_attribute(name)
        self._new[name] = value

    def _get_attribute(self, name: str) -> Any:
        self._assert_attribute(name)
        return self._new.get(name)

    def render(self, window, width: int = None, height: int = None) -> pygame.Surface:
        window: Window

        new_update = (window, width, height)
        if (
            self._surface is None
            or self._old != self._new
            or self._old_update != new_update
        ):
            self._debug("render")
            self._surface = self.draw(*new_update)
        self._old = self._new.copy()
        self._old_update = new_update
        return self._surface

    @abstractmethod
    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        raise NotImplementedError()


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


class Window:
    def __init__(self, title="Window", width=1280, height=720):
        self.title = title
        self.width = width
        self.height = height
        self.surfaces = []
        self.controls: List[Widget] = []
        self._running = True
        self._event_callbacks = {}
        self.__collect_event_callbacks()

    def __collect_event_callbacks(self):
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "event_type"):
                event_type = method.event_type
                assert event_type not in self._event_callbacks
                self._event_callbacks[event_type] = method

        pprint.pprint(
            {
                pygame.event.event_name(t): c.__name__
                for t, c in self._event_callbacks.items()
            }
        )

    def __on_event(self, event: Event):
        callback = self._event_callbacks.get(event.type)
        if callback is None:
            logging.debug(
                f"Unhandled pygame event: {pygame.event.event_name(event.type)}"
            )
            return False
        callback(event)
        return True

    def run(self):
        screen = pygame.display.set_mode(
            (self.width, self.height), flags=pygame.RESIZABLE
        )
        pygame.display.set_caption(self.title)
        clock = pygame.time.Clock()

        while self._running:
            for event in pygame.event.get():
                self.__on_event(event)
            screen_width, screen_height = screen.get_width(), screen.get_height()
            screen.fill("white")
            for control in self.controls:
                surface = control.render(self, screen_width, screen_height)
                screen.blit(surface, (0, 0))
            for surface in self.surfaces:
                screen.blit(surface, (0, 0))
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

    @on_event(pygame.QUIT)
    def _on_quit(self, event: Event):
        print("Quit pygame.")
        self._running = False


def main():
    title = (
        "Hello World!! "
        "αβαβαβαβαβ 【DETROIT】この選択がどう繋がっていくのか！？【#2】 "
        "모든 인간은 태어날 때부터 자유로우며"
    )

    pygame.init()
    text = "小松 未可子 | 🌀 hello world | " + Text.lorem_ipsum()
    window = Window(title=title)
    window.controls.append(Text(text, wrap=True))
    window.run()

    # running = True
    # while running:
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             print("Quit pygame.")
    #             running = False
    #     screen.fill("white")
    #     screen.blit(rdr, (0, 0))
    #     pygame.display.flip()
    #     clock.tick(60)
    # pygame.quit()


if __name__ == "__main__":
    main()
