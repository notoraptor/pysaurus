from abc import abstractmethod

import pygame

from videre import WINDOW_FPS
from videre.widgets.widget import Widget


class AbstractAnimation(Widget):
    __wprops__ = {}
    __slots__ = ("_clock", "_fps", "_delay_ms", "_spent_ms", "_nb_frames")

    def __init__(self, fps: int = 60, **kwargs):
        super().__init__(**kwargs)
        self._clock = pygame.time.Clock()
        self._fps = min(max(0, int(fps)), WINDOW_FPS)
        self._delay_ms = 1000 / self._fps
        self._spent_ms = 0
        self._nb_frames = 0

    def has_changed(self) -> bool:
        self._check_fps()
        return super().has_changed()

    def _check_fps(self):
        self._spent_ms += self._clock.tick()
        if self._spent_ms >= self._delay_ms:
            self._spent_ms = 0
            self._nb_frames += 1
            self._on_frame()

    @abstractmethod
    def _on_frame(self):
        raise NotImplementedError()
