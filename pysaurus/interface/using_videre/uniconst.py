from pysaurus.interface.using_videre.constants import Uniconst

if __name__ == "__main__":
    for name in dir(Uniconst):
        if not name.startswith("_"):
            print(name, getattr(Uniconst, name))
