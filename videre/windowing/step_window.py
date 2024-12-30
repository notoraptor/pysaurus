import io

import pygame

from videre.windowing.window import Window


class StepWindow(Window):
    __slots__ = ("_step_mode",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._step_mode = False

    def __enter__(self):
        if self._closed:
            raise RuntimeError("Window has already run. Cannot run again.")
        self._step_mode = True
        self._init_display()
        return self

    def render(self):
        if not self._step_mode:
            raise RuntimeError(f"render() requires step-mode (`with window`)")
        self._render()

    def screenshot(self) -> io.BytesIO:
        if not self._step_mode:
            raise RuntimeError(f"screenshot() requires step-mode (`with window`)")
        data = io.BytesIO()
        pygame.image.save(self._screen, data)
        data.flush()
        return data

    def snapshot(self) -> io.BytesIO:
        self.render()
        return self.screenshot()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._step_mode:
            self._step_mode = False
            self._closed = True
            pygame.quit()

    def run(self):
        if self._step_mode:
            raise RuntimeError("Window is in step mode. Cannot launch run().")
        return super().run()
