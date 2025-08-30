import multiprocessing
import threading
from types import SimpleNamespace

from wip.intersign import Intersign


def test_simple():
    counter = SimpleNamespace(value=0)

    def handler(value):
        counter.value += value

    assert counter.value == 0
    with Intersign.receiver():
        Intersign.handle_with(handler)
        Intersign.send(1)
        Intersign.send(1)
        Intersign.send(1)
        Intersign.send(1)
        Intersign.send(1)

    assert counter.value == 5


def test_multiple_threads():
    counter = SimpleNamespace(value=0)

    def handler(value):
        counter.value += value

    def run():
        Intersign.send(1)

    with Intersign.receiver():
        Intersign.handle_with(handler)

        threads = [threading.Thread(target=run) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert counter.value == 5


def run_process():
    Intersign.send(1)


def test_multiple_processes():
    counter = SimpleNamespace(value=0)

    def handler(value):
        counter.value += value

    with Intersign.receiver():
        Intersign.handle_with(handler)

        processes = [multiprocessing.Process(target=run_process) for _ in range(5)]
        for process in processes:
            process.start()
        for process in processes:
            process.join()

        assert counter.value == 5
