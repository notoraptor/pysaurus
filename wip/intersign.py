import multiprocessing
import threading
from typing import Any, Callable


class _Receiver:
    __slots__ = ("_manager", "_queue", "_thread", "_handler")

    def __init__(self):
        self._manager = multiprocessing.Manager()
        self._queue = self._manager.Queue()
        self._thread = None
        self._handler = None
        self.set_handler(None)

    def __enter__(self):
        if self._thread is None:
            th = threading.Thread(target=self._monitor)
            th.start()
            self._thread = th
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._thread
        self._queue.put(None)
        self._thread.join()
        self._thread = None

    def _monitor(self):
        print("[intersign] Receiving ...")
        while True:
            message = self._queue.get()
            if message is None:
                break
            self._handle(message)
        print("[intersign] ... Received.")

    def _handle(self, message: Any):
        self._handler(message)

    def set_handler(self, handler: Callable[[Any], None] | None):
        self._handler = handler or print

    def notify(self, message: Any):
        self._queue.put_nowait(message)


class Intersign:
    _receiver = None

    @classmethod
    def receiver(cls, handler: Callable[[Any], None] | None = None) -> _Receiver:
        """
        Start a thread to process all messages sent by sender().
        Must be able to capture all messages emitted by sender() from anywhere
        including threads and processes.
        """
        if cls._receiver is None:
            cls._receiver = _Receiver()
            cls._receiver.set_handler(handler)
        return cls._receiver

    @classmethod
    def send(cls, message: Any):
        """
        Emit message.
        Should be able to emit messages from anywhere, from threads to processes.
        All emitted messages should be received and managed in the thread started by
        receiver().

        There must be an automatic fallback management if receiver thread
        was not launched, for example: just print message into console.
        This means that there should exist a global variable to check
        to know whether receiver thread was started or not.
        """
        if cls._receiver is None:
            cls._default(message)
        else:
            cls._receiver.notify(message)

    @classmethod
    def handle_with(cls, handler: Callable[[Any], None] | None):
        if cls._receiver is None:
            raise RuntimeError(
                "Receiver not started. "
                "Please use `with Intersign.receiver()` first. "
                "You can also initialize receiver with handler: "
                "`with Intersign.receiver(handler=handler)`"
            )
        cls._receiver.set_handler(handler)

    @classmethod
    def _default(cls, message: Any):
        print(f"[{cls.__name__}] {message}")


def example():
    Intersign.send("hello")
    with Intersign.receiver():
        Intersign.send("message 1")
        Intersign.send("message 2")
        Intersign.send("message 3")


if __name__ == "__main__":
    example()
