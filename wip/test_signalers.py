import multiprocessing
import threading
from types import SimpleNamespace

import pytest

from wip.filesignaling import Watching
from wip.talking import Talk


class IntersignFile:
    receiver = Watching.listen
    handle_with = receiver
    send = Watching.notify


class IntersignListener:
    receiver = Talk.listen
    handle_with = receiver
    send = Talk.notify


def run_process(signaler):
    signaler.send(1)


@pytest.mark.parametrize("signaler", (IntersignFile, IntersignListener))
class TestSignaler:
    def test_simple(self, signaler):
        counter = SimpleNamespace(value=0)

        def handler(value):
            counter.value += value

        assert counter.value == 0
        with signaler.receiver():
            signaler.handle_with(handler)
            signaler.send(1)
            signaler.send(1)
            signaler.send(1)
            signaler.send(1)
            signaler.send(1)

        assert counter.value == 5

    def test_multiple_threads(self, signaler):
        counter = SimpleNamespace(value=0)

        def handler(value):
            counter.value += value

        def run():
            signaler.send(1)

        with signaler.receiver():
            signaler.handle_with(handler)

            threads = [threading.Thread(target=run) for _ in range(5)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        assert counter.value == 5

    def test_multiple_processes(self, signaler):
        counter = SimpleNamespace(value=0)

        def handler(value):
            counter.value += value

        with signaler.receiver():
            signaler.handle_with(handler)

            processes = [
                multiprocessing.Process(target=run_process, args=(signaler,))
                for _ in range(5)
            ]
            for process in processes:
                process.start()
            for process in processes:
                process.join()

        assert counter.value == 5
