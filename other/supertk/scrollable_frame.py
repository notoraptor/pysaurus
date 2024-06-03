import sys
import tkinter
from tkinter import ttk

from other.supertk.supertk import Sticky, SystemName

_SCROLLFRAME_IN = "<<ScrollFrameIn>>"
_SCROLLFRAME_OUT = "<<ScrollFrameOut>>"
_SCROLLCANVAS_IN = "<<ScrollCanvasIn>>"
_SCROLLCANVAS_OUT = "<<ScrollCanvasOut>>"


class Example(ttk.Frame):
    """
    2024/06/02
    https://stackoverflow.com/a/3092341

    React to mousewheel events:
    https://stackoverflow.com/a/17457843
    https://stackoverflow.com/a/37858368
    """

    _MW_SEQUENCES = (
        ["<Button-4>", "<Button-5>"]
        if sys.platform == SystemName.LINUX
        else ["<MouseWheel>"]
    )

    def __init__(self, parent):
        super().__init__(parent)
        self._in_frame = False
        self._in_canvas = False
        self._bound = False
        self._mousewheel_func_ids = []

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
        # root.bind(_SCROLLCANVAS_IN, self._on_scroll_canvas_in, add=True)
        # root.bind(_SCROLLCANVAS_OUT, self._on_scroll_canvas_out, add=True)

        self.populate()

    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_enter_frame(self, event):
        self._in_frame = True
        self.event_generate(_SCROLLFRAME_IN)

    def _on_leave_frame(self, event):
        self._in_frame = False
        self.event_generate(_SCROLLFRAME_OUT)

    def _on_enter_canvas(self, event):
        self._in_canvas = True
        self._canvas.event_generate(_SCROLLCANVAS_IN)
        self._bound_to_mousewheel()

    def _on_leave_canvas(self, event):
        self._in_canvas = False
        self._canvas.event_generate(_SCROLLFRAME_OUT)
        self._unbound_to_mousewheel()

    def _bound_to_mousewheel(self):
        if self._bound:
            return
        self._mousewheel_func_ids = [
            self.winfo_toplevel().bind(sequence, self._on_mousewheel, add="+")
            for sequence in self._MW_SEQUENCES
        ]
        print("Bound", self._mousewheel_func_ids)
        self._bound = True

    def _unbound_to_mousewheel(self):
        if not self._bound:
            return
        print("Unbound", self._mousewheel_func_ids)
        for sequence in self._MW_SEQUENCES:
            for func_id in self._mousewheel_func_ids:
                self.winfo_toplevel().unbind(sequence, func_id)
        self._bound = False

    def _on_mousewheel(self, event: tkinter.Event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _on_scroll_frame_in(self, event: tkinter.Event):
        if event.widget is not self and self._in_frame:
            # There is a scroll frame inside this scroll frame
            # in which mouse just entered. We stop monitoring mouse wheels
            self._unbound_to_mousewheel()

    def _on_scroll_frame_out(self, event: tkinter.Event):
        print("on scroll frame", event.widget, self, self._in_frame)
        if event.widget is not self and self._in_frame:
            # There is a scroll frame inside this scroll frame
            # from which mouse just exited. We restart monitoring mouse wheels
            self._bound_to_mousewheel()

    def _on_scroll_area_in(self, event: tkinter.Event):
        print("on scroll area in", event.widget is self._canvas, event.widget)
        if event.widget is not self._canvas:
            if self._in:
                # There is a scroll area inside this scroll area
                # in which mouse just entered. We stop monitoring mouse wheels
                self._unbound_to_mousewheel()

    def _on_scroll_area_out(self, event):
        print("on scroll area out", event.widget is self._canvas, event.widget)
        if event.widget is not self._canvas:
            if self._in:
                # There is a scroll area inside this scroll area
                # from which mouse just exited. We restart monitoring mouse wheels
                self._bound_to_mousewheel()

    def populate(self):
        """Put in some fake data"""
        size = 100
        for i in range(size):
            ttk.Label(self.frame, text=f"Element {i + 1} on {size}").grid()
