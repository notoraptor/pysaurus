import tkinter


class Window:
    __slots__ = ("_root",)

    def __init__(self):
        self._root = tkinter.Tk()
        self._root.geometry("1280x720")
        self._center_window()

    def _center_window(self):
        """
        2024/06/02
        https://stackoverflow.com/a/76796149
        """
        # This seems to just center top-left corner of window, not window itself.
        # self._root.eval("tk::PlaceWindow . center")
        # Instead we use code below.
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        win_width = 1280
        win_height = 720
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        print(screen_width, screen_height)
        self._root.geometry(f"{win_width}x{win_height}+{x}+{y}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._root.mainloop()

    @property
    def root(self) -> tkinter.Tk:
        return self._root
