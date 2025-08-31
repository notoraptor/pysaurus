import dataclasses
import json
import threading
from dataclasses import dataclass
from multiprocessing.connection import Client, Listener
from pathlib import Path
from typing import Any, Callable


def _get_sentinel_path() -> Path:
    file_title = f".{Path(__file__).resolve().stem}"
    return Path(f"./{file_title}.sentinel").resolve()


@dataclass(slots=True)
class _Config:
    address: str = "localhost"
    port: int = 6000

    def to_tuple(self) -> tuple[str, int]:
        return (self.address, self.port)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _get_config() -> _Config:
    file_title = f".{Path(__file__).resolve().stem}"
    config_path = Path(f"./{file_title}.config.json").resolve()
    if config_path.is_file():
        with open(config_path, mode="r", encoding="utf-8") as f:
            config_dict = json.load(f)
            config = _Config(**config_dict)
    else:
        config = _Config()
        with open(config_path, mode="w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f)
    return config


class _Monitoring:
    __sentinel__ = _get_sentinel_path()
    __address__ = _get_config().to_tuple()
    __monitor__ = None

    @classmethod
    def _create_sentinel(cls):
        with open(cls.__sentinel__, mode="w"):
            pass

    @classmethod
    def _remove_sentinel(cls):
        if cls.__sentinel__.exists():
            cls.__sentinel__.unlink()

    def __init__(self):
        self._handler = None
        self._listener = None
        self._thread = None
        self.set_handler(None)

    def set_handler(self, handler: Callable[[Any], None] | None):
        """Set message handler. Default is print."""
        self._handler = handler or print

    def __enter__(self):
        if self._thread is None:
            self._listener = Listener(address=self.__address__)
            self._create_sentinel()
            self._thread = threading.Thread(target=self._monitor)
            self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._thread is not None
        self.notify(None)
        self._thread.join()
        self._listener.close()
        self._listener = None
        self._thread = None

    def _monitor(self):
        print("Monitoring...")
        try:
            while True:
                with self._listener.accept() as conn:
                    message = conn.recv()
                    if message is None:
                        break
                    self._handler(message)
        finally:
            self._remove_sentinel()
            print("... Monitored")

    @classmethod
    def notify(cls, message: Any):
        if cls.__sentinel__.exists():
            try:
                with Client(address=cls.__address__) as conn:
                    conn.send(message)
            except ConnectionRefusedError:
                cls._fallback(message)
        else:
            cls._fallback(message)

    @classmethod
    def _fallback(cls, message: Any):
        print("[talk]", message)


class Talk:
    @classmethod
    def listen(cls, handler: Callable[[Any], None] | None = None) -> _Monitoring:
        if _Monitoring.__monitor__ is None:
            _Monitoring.__monitor__ = _Monitoring()
        monitor = _Monitoring.__monitor__
        monitor.set_handler(handler)
        return monitor

    @classmethod
    def notify(cls, message: Any):
        _Monitoring.notify(message)
