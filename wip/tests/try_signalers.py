from wip.filesignaling import Watching
from wip.talking import Talk


def demo_signaler(signaler):
    signaler.notify(0)
    with signaler.listen():
        signaler.notify(0)
        signaler.notify(1)
        signaler.notify(2)
        signaler.notify(3)
        signaler.notify(4)
    signaler.notify(0)


def main():
    for signaler in (Watching, Talk):
        print(f"{{{signaler.__name__}}}")
        demo_signaler(signaler)
        print()


if __name__ == "__main__":
    main()
