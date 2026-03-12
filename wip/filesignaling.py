import inspect
import json
import threading
import time
from pathlib import Path
from typing import Any, Callable

from filelock import SoftFileLock


def _get_file_path() -> Path:
    """
    Get path of file to use for signal processing.

    File name must be the same as this script, prepended with "." .
    File folder must be working directory.
    """
    module_path = Path(__file__).resolve()
    module_title = module_path.stem
    file_title = f".{module_title}"
    file_path = Path(f"./{file_title}").resolve()
    return file_path


def _get_lock_file_path() -> Path:
    file_path = _get_file_path()
    return file_path.with_stem(f"{file_path.stem}.lock")


class _FileMonitoring:
    __slots__ = ("_handler", "_thread")
    __file_path__ = _get_file_path()
    __lock_path__ = _get_lock_file_path()
    __monitor__ = None

    def __init__(self):
        self._handler = None
        self._thread = None
        self.set_handler(None)

    def set_handler(self, handler: Callable[[Any], None] | None):
        """Set message handler. Default is print."""
        self._handler = handler or print

    def __enter__(self):
        with open(self.__file_path__, mode="w", encoding="utf-8"):
            # Make sure signaling file exists.
            # Truncate him if already present.
            pass
        if self._thread is None:
            # Launch monitoring thread.
            thread = threading.Thread(target=self._monitor)
            thread.start()
            self._thread = thread
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Signaling file should exist.
        assert self.__file_path__.is_file()
        # Notify with `None` to terminate monitoring thread.
        self.notify(None)
        # Wait for monitoring thread to terminate.
        self._thread.join()
        self._thread = None
        # Delete signaling file.
        self.__file_path__.unlink()
        assert not self.__file_path__.exists()

    def _monitor(self):
        """
        Monitoring method.
        Read signaling file forever, line by line.
        Parse line using json.
        Terminate if None is parsed.
        Otherwise, call handler with parsed data.
        """
        print("Monitoring...")
        with open(self.__file_path__, mode="r") as file:
            while True:
                line = file.readline().strip()
                if line:
                    message = json.loads(line)
                    if message is None:
                        break
                    self._handler(message)
                else:
                    time.sleep(1 / 1_000_000)
        print("... Monitored.")

    @classmethod
    def notify(cls, message: Any):
        # Ue a file lock to write in signaling file
        # Set timeout to -1 to block until signaling file is available
        with SoftFileLock(cls.__lock_path__, timeout=-1):
            with open(cls.__file_path__, mode="a", encoding="utf-8") as f:
                f.write(json.dumps(message, default=cls._serialize) + "\n")

    @classmethod
    def _serialize(cls, message: Any) -> Any:
        for name in ("json", "dict", "to_json", "to_dict"):
            method = getattr(message, name, None)
            if method is not None and inspect.ismethod(method):
                return method()
        return str(message)


class Watching:
    @classmethod
    def listen(cls, handler: Callable[[Any], None] | None = None) -> _FileMonitoring:
        if _FileMonitoring.__monitor__ is None:
            _FileMonitoring.__monitor__ = _FileMonitoring()
        monitor = _FileMonitoring.__monitor__
        monitor.set_handler(handler)
        return monitor

    @classmethod
    def notify(cls, message: Any):
        if _FileMonitoring.__file_path__.is_file():
            _FileMonitoring.notify(message)
        else:
            print("[watching]", message)
