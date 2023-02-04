from multiprocessing import Process

from pysaurus.core import notifications, notifying


class Handler1:
    def __call__(self, n):
        print("Handler 1", n)


class Handler2:
    def __call__(self, n):
        print("Handler 2", n)


def run1():
    notifying.notify(notifications.Message("msg1"))
    notifying.notify(notifications.Message("msg2"))


def main():
    handler1 = Handler1()
    handler2 = Handler2()
    notifying.config(handler=handler1)
    p = Process(target=notifying.with_handler, args=(handler2, run1))
    p.start()
    p.join()


if __name__ == "__main__":
    main()
