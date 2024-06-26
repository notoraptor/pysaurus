import tkinter
from tkinter import font as tk_font


class Window:
    __slots__ = ("_root", "_windowing_system")

    def __init__(self):
        self._root = tkinter.Tk()
        self._windowing_system = self._root.tk.call("tk", "windowingsystem")
        self._center_window()
        self._set_fonts()
        # (2024/06/03) https://tkdocs.com/tutorial/menus.html
        self._root.option_add("*tearOff", False)

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

    @classmethod
    def _set_fonts(cls):
        f = tk_font.nametofont("TkDefaultFont")
        size = f.actual()["size"]
        f.configure(size=max(size, 12))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._root.mainloop()

    @property
    def root(self) -> tkinter.Tk:
        return self._root

    @property
    def windowying_system(self) -> str:
        return self._windowing_system
