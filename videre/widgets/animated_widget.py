import pygame

from videre.widgets.widget import Widget


class AnimatedWidget(Widget):
    __slots__ = ("_clock", "_fps", "_delay_ms", "_spent_ms", "_nb_frames")

    def __init__(self, framerate: int = 60, **kwargs):
        super().__init__(**kwargs)
        self._clock = pygame.time.Clock()
        self._fps = min(max(0, int(framerate)), 1000)
        self._delay_ms = 1000 / self._fps
        self._spent_ms = 0
        self._nb_frames = 0

    @property
    def frame_rank(self) -> int:
        return self._nb_frames

    def has_changed(self) -> bool:
        return self._has_fps() or super().has_changed()

    def _has_fps(self):
        self._spent_ms += self._clock.tick()
        if self._spent_ms >= self._delay_ms:
            self._spent_ms = 0
            self._nb_frames += 1
            print("fps", self._nb_frames)
            return True
        return False

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        return self._new_surface(10, 10)
