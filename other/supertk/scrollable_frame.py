import tkinter
from tkinter import ttk

from other.supertk.supertk import Sticky

_SCROLLFRAME_IN = "<<ScrollFrameIn>>"
_SCROLLFRAME_OUT = "<<ScrollFrameOut>>"

# For Windows
_MOUSEWHEEL = "<MouseWheel>"
# For Linux
_BUTTON_4 = "<Button-4>"
_BUTTON_5 = "<Button-5>"


class ScrollableFrame(ttk.Frame):
    """
    2024/06/02
    https://stackoverflow.com/a/3092341

    React to mousewheel events:
    https://stackoverflow.com/a/17457843
    https://stackoverflow.com/a/37858368
    """

    def __init__(self, parent, name=None):
        super().__init__(parent)
        self._name = name or str(id(self))
        self._in_frame = False
        self._bound = False
        self._mw_func_indices = {}

        self._canvas = tkinter.Canvas(self, borderwidth=0)
        self.frame = ttk.Frame(self._canvas)
        self._v_scrollbar = ttk.Scrollbar(
            self, orient=tkinter.VERTICAL, command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=self._v_scrollbar.set)

        self._canvas.grid(row=0, column=0, sticky=Sticky.FULL)
        self._v_scrollbar.grid(row=0, column=1, sticky=Sticky.VERTICAL)
        self._canvas.create_window(
            (0, 0),
            window=self.frame,
            anchor=(Sticky.TOP + Sticky.LEFT),
            tags="self.frame",
        )

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.frame.bind("<Configure>", self._on_frame_configure)
        self.bind("<Enter>", self._on_enter_frame)
        self.bind("<Leave>", self._on_leave_frame)
        self._canvas.bind("<Enter>", self._on_enter_canvas)
        self._canvas.bind("<Leave>", self._on_leave_canvas)

        root = self.winfo_toplevel()
        root.bind(_SCROLLFRAME_IN, self._on_scroll_frame_in, add=True)
        root.bind(_SCROLLFRAME_OUT, self._on_scroll_frame_out, add=True)

        self.populate()

    def __debug(self, *args):
        print(f"Scrollable[{self._name}]", *args)

    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_enter_frame(self, event):
        # self.__debug("enter frame")
        self._in_frame = True
        self.event_generate(_SCROLLFRAME_IN)

    def _on_leave_frame(self, event):
        # self.__debug("leave frame")
        self._in_frame = False
        self.event_generate(_SCROLLFRAME_OUT)

    def _on_enter_canvas(self, event):
        # self.__debug("enter canvas")
        self._bound_to_mousewheel()

    def _on_leave_canvas(self, event):
        # self.__debug("leave canvas")
        self._unbound_to_mousewheel()

    def _bound_to_mousewheel(self):
        if self._bound:
            return
        # self.__debug("bound")
        root = self.winfo_toplevel()
        self._mw_func_indices = {
            _MOUSEWHEEL: root.bind(_MOUSEWHEEL, self._on_mousewheel, "+"),
            _BUTTON_4: root.bind(_BUTTON_4, self._on_button_4, "+"),
            _BUTTON_5: root.bind(_BUTTON_5, self._on_button_5, "+"),
        }
        self._bound = True

    def _unbound_to_mousewheel(self):
        if not self._bound:
            return
        # self.__debug("unbound")
        root = self.winfo_toplevel()
        for sequence, func_id in self._mw_func_indices.items():
            root.unbind(sequence, func_id)
        self._bound = False

    def _on_mousewheel(self, event: tkinter.Event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_button_4(self, event: tkinter.Event):
        self._canvas.yview_scroll(-1, "units")

    def _on_button_5(self, event: tkinter.Event):
        self._canvas.yview_scroll(1, "units")

    def _on_scroll_frame_in(self, event: tkinter.Event):
        if event.widget is not self and self._in_frame:
            # self.__debug("(captured in child)")
            # There is a scroll frame inside this scroll frame
            # in which mouse just entered. We stop monitoring mouse wheels
            self._unbound_to_mousewheel()

    def _on_scroll_frame_out(self, event: tkinter.Event):
        if event.widget is not self and self._in_frame:
            # self.__debug("(exited from child)", event.widget, self)
            # There is a scroll frame inside this scroll frame
            # from which mouse just exited. We restart monitoring mouse wheels
            self._bound_to_mousewheel()

    def populate(self):
        """Put in some fake data"""
        size = 100
        for i in range(size):
            ttk.Label(self.frame, text=f"Element {i + 1} on {size}").grid()
