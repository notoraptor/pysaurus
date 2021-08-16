"""
padding: right top left bottom
"""
from collections import namedtuple
from tkinter import *
from tkinter import ttk


class _TkOption(
    namedtuple("_TkOption", ("name", "db_name", "db_class", "default", "current"))
):
    pass


def check_version():
    expected_version = [8, 6]
    current_version = [int(v) for v in Tcl().eval("info patchlevel").split(".")]
    assert current_version >= expected_version
    assert Tcl().eval('set tcl_platform(threaded)'), (
        "This build of Tkinter does not support threading."
    )


def tk_help(widget: Widget):
    return {name: _TkOption(*options) for name, options in widget.configure()}


class FeetToMeters:
    def __init__(self, root):
        root.title("Feets to meters")

        main_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
        main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        # Fill all root space in column and row.
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=1)

        self.feet = StringVar()
        feet_entry = ttk.Entry(main_frame, width=10, textvariable=self.feet)
        feet_entry.grid(column=2, row=1, sticky=(W, E))

        self.meters = StringVar()
        ttk.Label(main_frame, textvariable=self.meters).grid(
            column=2, row=2, sticky=(W, E)
        )

        ttk.Button(main_frame, text="Calculate", command=self.calculate).grid(
            column=3, row=3, sticky=W
        )

        ttk.Label(main_frame, text="feet").grid(column=3, row=1, sticky=W)
        ttk.Label(main_frame, text="is equivalent to").grid(column=1, row=2, sticky=E)
        ttk.Label(main_frame, text="meters").grid(column=3, row=2, sticky=W)

        self.v = StringVar(value="b")
        self.el = ttk.Combobox(
            main_frame, textvariable=self.v, values=("a", "b", "c"), state="readonly"
        )
        self.el.grid(column=1, row=3, sticky=(W, S))

        self.cb = BooleanVar(value=True)

        def on_toggle(*args):
            if self.cb.get():
                print("display")
                self.el.grid()
            else:
                print("remove")
                self.el.grid_remove()

        c = ttk.Checkbutton(main_frame, text="togglen", command=on_toggle, variable=self.cb)
        c.grid(column=2, row=3)

        for child in main_frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

        feet_entry.focus()
        root.bind("<Return>", self.calculate)

    def calculate(self, *args):
        try:
            value = float(self.feet.get())
            self.meters.set(int(0.3048 * value * 10000.0 + 0.5) / 10000.0)
        except ValueError:
            pass


def main():
    check_version()
    root = Tk()
    FeetToMeters(root)
    root.mainloop()


if __name__ == "__main__":
    main()
