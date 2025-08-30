import pickle
import threading
from contextlib import contextmanager
from typing import Any

import zmq


class Siginter:
    _receiver_active = False
    _context = None
    _socket_push = None
    _socket_pull = None
    _thread = None
    _stop_event = None
    _address = "inproc://siginter"

    @classmethod
    def _ensure_context(cls):
        if cls._context is None:
            cls._context = zmq.Context()

    @classmethod
    def _receiver_loop(cls):
        cls._ensure_context()
        socket = cls._context.socket(zmq.PULL)
        socket.bind(cls._address)
        cls._socket_pull = socket

        while not cls._stop_event.is_set():
            try:
                if socket.poll(100):  # 100ms timeout
                    message_bytes = socket.recv(zmq.NOBLOCK)
                    message = pickle.loads(message_bytes)
                    print(f"Received: {message}")
            except zmq.Again:
                continue
            except Exception as e:
                print(f"Error in receiver: {e}")

        socket.close()

    @classmethod
    @contextmanager
    def receiver(cls):
        """
        Start a thread to process all messages sent by sender().
        Must be able to capture all messages emitted by sender() from anywhere
        including threads and processes.
        """
        if cls._receiver_active:
            yield
            return

        cls._ensure_context()
        cls._receiver_active = True
        cls._stop_event = threading.Event()
        cls._thread = threading.Thread(target=cls._receiver_loop, daemon=True)
        cls._thread.start()

        try:
            yield
        finally:
            cls._receiver_active = False
            if cls._stop_event:
                cls._stop_event.set()
            if cls._thread:
                cls._thread.join(timeout=1.0)
            if cls._socket_pull:
                cls._socket_pull.close()
                cls._socket_pull = None
            cls._stop_event = None
            cls._thread = None

    @classmethod
    def sender(cls, message: Any):
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
        if not cls._receiver_active:
            print(f"Fallback: {message}")
            return

        try:
            cls._ensure_context()
            if cls._socket_push is None:
                cls._socket_push = cls._context.socket(zmq.PUSH)
                cls._socket_push.connect(cls._address)

            message_bytes = pickle.dumps(message)
            cls._socket_push.send(message_bytes, zmq.NOBLOCK)

        except Exception as e:
            print(f"Error sending message, fallback: {message} (Error: {e})")


def example():
    with Siginter.receiver():
        Siginter.sender("message 1")
        Siginter.sender("message 2")
        Siginter.sender("message 3")


if __name__ == "__main__":
    example()
