from tkinter import Tk, filedialog


class TkContext:
    __slots__ = ("root",)

    def __init__(self, topmost=True):
        self.root = Tk()
        self.root.withdraw()
        if topmost:
            self.root.attributes("-topmost", True)

    def get_display_size(self) -> tuple[int, int]:
        """
        (2024/05/22)
        https://stackoverflow.com/a/66248631
        """
        self.root.update_idletasks()
        self.root.attributes("-fullscreen", True)
        self.root.state("iconic")
        # width, height = self.root.maxsize()
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        return width, height

    def close(self):
        self.root.destroy()
        print("Closed tk context")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def _string_or_empty(value):
    # On Linux, if no path is selected for file or directory,
    # it may return an empty tuple instead of a string.
    # Make sure to return a string in any case.
    return value if isinstance(value, str) else ""


def select_directory(default=None) -> str:
    with TkContext():
        return _string_or_empty(
            filedialog.askdirectory(mustexist=True, initialdir=default)
        )


def select_file_to_open() -> str:
    with TkContext():
        return _string_or_empty(filedialog.askopenfilename())


def select_many_files_to_open():
    with TkContext():
        return filedialog.askopenfilenames()


def select_file_to_save() -> str:
    with TkContext():
        return _string_or_empty(filedialog.asksaveasfilename())


def clipboard_set(text: str) -> None:
    with TkContext() as ctx:
        ctx.root.clipboard_clear()
        ctx.root.clipboard_append(text)
        ctx.root.update()


def clipboard_get() -> str:
    with TkContext() as ctx:
        return ctx.root.clipboard_get()


# unused
def get_screen_size() -> tuple[int, int]:
    """Return (width, height) of screen."""
    with TkContext() as ctx:
        return ctx.get_display_size()
