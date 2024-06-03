import tkinter


class Window:
    __slots__ = ("_root",)

    def __init__(self):
        self._root = tkinter.Tk()
        self._root.geometry("1280x720")
        # This seems to just center top-left corner of window, not window itself.
        # self._root.update()
        # self._root.eval("tk::PlaceWindow . center")
        self._center_window()

    def _center_window(self):
        """
        2024/06/02
        https://stackoverflow.com/a/76796149
        """
        self._root.update()
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        border_width = self._root.winfo_rootx() - self._root.winfo_x()
        title_height = self._root.winfo_rooty() - self._root.winfo_y()
        win_width = self._root.winfo_width() + 2 * border_width
        win_height = self._root.winfo_height() + title_height + border_width
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        print(screen_width, screen_height)
        print(win_width, win_height)
        self._root.geometry(f"+{x}+{y}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._root.mainloop()

    @property
    def root(self) -> tkinter.Tk:
        return self._root
