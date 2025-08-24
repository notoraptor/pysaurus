from typing import Any, Callable, Literal

from videre.core.pygame_utils import Event


def on_event(event_type: int):
    """
    Generate a decorator to mark a function as an event manager for given event type.
    Used on Window's event handling methods.

    :param event_type: Pygame event type.
    :return: a decorator
    """

    def decorator(function):
        function.event_type = event_type
        return function

    return decorator


class OnEvent:
    __slots__ = ("_callbacks",)

    def __init__(self) -> None:
        self._callbacks: dict[int, Callable[[Any, Event], Literal[True] | None]] = {}

    def __call__(self, event_type: int):
        assert event_type not in self._callbacks

        def decorator(function):
            function.event_type = event_type
            self._callbacks[event_type] = function
            return function

        return decorator

    def __str__(self):
        return str({et: f.__name__ for et, f in self._callbacks.items()})

    def __len__(self):
        return len(self._callbacks)

    def get(self, event_type: int) -> Callable[[Any, Event], bool] | None:
        return self._callbacks.get(event_type, None)


class WidgetByKeyGetter:
    __slots__ = ("key",)

    def __init__(self, key: str):
        self.key = key

    def __call__(self, widget) -> bool:
        return widget.key == self.key
