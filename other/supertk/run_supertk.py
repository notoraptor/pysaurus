import pprint
import tkinter
from tkinter import ttk

from other.supertk.constants import LOREM_IPSUM
from other.supertk.event import my_event
from other.supertk.scrollable_frame import ScrollableFrame
from other.supertk.supertk import (
    BorderRelief,
    Sticky,
    TCL_THREADED,
    TCL_VERSION,
    TK_VERSION,
    open_image,
    padding,
)
from other.supertk.window import Window


class MyApp:
    def __init__(self, root: tkinter.Tk):
        main_frame = ttk.Frame(root, padding=padding(5, 5, 5, 5))
        main_frame.grid(column=0, row=0, sticky=Sticky.FULL)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.feet = tkinter.StringVar()
        feet_entry = ttk.Entry(main_frame, width=7, textvariable=self.feet)
        feet_entry.grid(column=2, row=1, sticky=Sticky.HORIZONTAL)

        self.meters = tkinter.StringVar()
        ttk.Label(main_frame, textvariable=self.meters).grid(
            column=2, row=2, sticky=Sticky.HORIZONTAL
        )

        ttk.Button(main_frame, text="Calculate!", command=self.calculate).grid(
            column=3, row=3, sticky=tkinter.E
        )

        ttk.Label(main_frame, text="feet").grid(column=3, row=1, sticky=tkinter.W)
        ttk.Label(main_frame, text="is equivalent to:").grid(
            column=1, row=2, sticky=tkinter.E
        )
        ttk.Label(main_frame, text="meters").grid(column=3, row=2, sticky=tkinter.W)

        for child in main_frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

        feet_entry.focus()
        root.bind("<Return>", self.calculate)

    def calculate(self, *args):
        try:
            value = float(self.feet.get())
            self.meters.set(str(int(0.3048 * value * 10000.0 + 0.5) / 10000.0))
        except ValueError:
            pass


def main():
    root = tkinter.Tk()
    root.title("This is the window title!")
    MyApp(root)
    root.mainloop()


def display_widget_info(widget):
    options = {}
    # One info is a 5-tuple with format:
    # (name, db option name (?), db option class (?), default value, current value)
    for name, (_, _, _, default_value, current_value) in widget.configure().items():
        options[name] = {"default": default_value, "value": current_value}
    print(pprint.pformat({"class": widget.winfo_class(), "options": options}))


def check_widget_help():
    root = tkinter.Tk()
    button = ttk.Button(root, text="my button")

    print(button["text"])
    button["text"] = "something"
    print(button["text"])
    button.configure(text="tralala")
    print(button["text"])
    # Display option info: name, _, _, default value, current value
    print(button.configure("text"))
    # Display info of all options available for given widget.
    print(button.configure())
    display_widget_info(button)

    button.grid()

    def on_mouse_wheel(e: tkinter.Event):
        # print(e)
        print(my_event(e))

    root.bind("<MouseWheel>", on_mouse_wheel)
    root.bind("<KeyPress>", on_mouse_wheel)
    root.mainloop()


def check_label():
    with Window() as window:
        # (2024/06/01)
        # https://www.geeksforgeeks.org/loading-images-in-tkinter-using-pil/
        # NB: We may need to keep a reference (i.e. not inline open_image())
        # so that label has time to display it.
        image = open_image("image.jpg")
        ttk.Label(window.root, image=image).grid()
        ttk.Label(window.root, text=LOREM_IPSUM, wraplength=1000).grid()


def check_combobox():
    with Window() as window:
        value = tkinter.StringVar(value="bbb")
        combo = ttk.Combobox(
            window.root, textvariable=value, values=["aaa", "bbb", "ccc"]
        )
        # Force user to choose between given values (forbid user to enter nee value)
        combo.state(["readonly"])
        combo.grid()

        def on_selection(*args):
            print("on selection", *args)

        window.root.bind("<<ComboboxSelected>>", on_selection)


def check_grid():
    """
    0 0 5 5
    0 0 6 6
    0 0 7 7
    0 0 7 7
    1 2 3 4
    """
    with Window() as window:
        root = window.root
        content = ttk.Frame(root, borderwidth=40, relief=BorderRelief.SOLID)
        content.grid(row=0, column=0, sticky=Sticky.FULL)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        frames = [
            ttk.Frame(content, borderwidth=4, relief=BorderRelief.RIDGE)
            for _ in range(8)
        ]
        texts = [ttk.Label(frame, text=f"frame {i}") for i, frame in enumerate(frames)]
        for text in texts:
            text.grid()
        frames[0].grid(
            row=1, column=1, rowspan=4, columnspan=2, sticky=(Sticky.TOP, Sticky.LEFT)
        )
        content.columnconfigure(1, weight=1)
        # content.columnconfigure(2, weight=1)
        content.rowconfigure(1, weight=1)
        frames[1].grid(row=1, column=3, columnspan=2, sticky=(Sticky.TOP, Sticky.LEFT))
        frames[2].grid(row=2, column=3, columnspan=2, sticky=(Sticky.TOP, Sticky.LEFT))
        frames[3].grid(
            row=3, column=3, rowspan=2, columnspan=2, sticky=(Sticky.TOP, Sticky.LEFT)
        )
        frames[4].grid(row=5, column=1, sticky=(Sticky.TOP, Sticky.LEFT))
        frames[5].grid(row=5, column=2, sticky=(Sticky.TOP, Sticky.LEFT))
        frames[6].grid(row=5, column=3, sticky=(Sticky.TOP, Sticky.LEFT))
        frames[7].grid(row=5, column=4, sticky=(Sticky.TOP, Sticky.LEFT))
        ttk.Label(content, text="placeholder 1").grid(
            row=3, column=5, sticky=(Sticky.TOP, Sticky.LEFT)
        )
        ttk.Label(content, text="placeholder 2").grid(
            row=4, column=5, sticky=(Sticky.TOP, Sticky.LEFT)
        )


def check_scrollbar_with_listbox():
    with Window() as window:
        root = window.root
        content = ttk.Frame(root, borderwidth=10, relief=BorderRelief.RIDGE)
        content.grid(row=0, column=0, sticky=Sticky.FULL)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        list_size = 200
        list_values = [f"Element {i + 1} / {list_size}" for i in range(list_size)]
        list_var = tkinter.StringVar(value=list_values)
        list_box = tkinter.Listbox(content, height=5, listvariable=list_var)
        list_box.grid(row=0, column=0, sticky=Sticky.FULL)

        scrollbar = ttk.Scrollbar(
            content, orient=tkinter.VERTICAL, command=list_box.yview
        )
        scrollbar.grid(row=0, column=1, sticky=Sticky.VERTICAL)
        list_box.configure(yscrollcommand=scrollbar.set)


def check_scrollbar_with_frame():
    with Window() as window:
        root = window.root
        content = ttk.Frame(root)
        content.grid(row=0, column=0, sticky=Sticky.FULL)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        eg = ScrollableFrame(content, name="parent__")
        eg.grid(row=0, column=0, sticky=Sticky.FULL)
        sbeg = ScrollableFrame(eg.frame, name="children")
        sbeg.configure(width=300, height=300)
        sbeg.grid()
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)


def check_menu():
    with Window() as window:
        root = window.root
        menubar = tkinter.Menu(root)
        root.configure(menu=menubar)

        menu_file = tkinter.Menu(menubar)
        menu_file.add_command(label="New ...")
        menu_file.add_command(label="Open ...")
        menu_file.add_command(label="Close!")

        menu_recent = tkinter.Menu(menu_file)
        menu_file.add_cascade(menu=menu_recent, label="Recent ...")
        for i in range(10):
            menu_recent.add_command(label=f"File {i + 1}", command=lambda : print("Selected recent", i + 1))
        menu_file.add_separator()
        menu_file.add_command(label="after separator")

        check = tkinter.StringVar()
        menu_file.add_checkbutton(label='Check', variable=check, onvalue=1, offvalue=0)
        radio = tkinter.StringVar()
        menu_file.add_radiobutton(label='One', variable=radio, value=1)
        menu_file.add_radiobutton(label='Two', variable=radio, value=2)

        menu_edit = tkinter.Menu(menubar)
        menubar.add_cascade(menu=menu_file, label="File")
        menubar.add_cascade(menu=menu_edit, label='Edit')


if __name__ == "__main__":
    print("Tkinter version:", TK_VERSION)
    print("Tcl/Tk version:", TCL_VERSION)
    print("Tcl/Tk threaded:", TCL_THREADED)
    # check_widget_help()
    # check_label()
    # check_combobox()
    # check_grid()
    check_scrollbar_with_frame()
    # check_menu()
