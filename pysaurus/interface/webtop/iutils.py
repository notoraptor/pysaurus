from tkinter import Tk, filedialog


_root = Tk()
_root.withdraw()
_root.attributes('-topmost', True)


def select_directory():
    return filedialog.askdirectory()


def select_file_to_open():
    return filedialog.askopenfilename()


def select_many_files_to_open():
    return filedialog.askopenfilenames()


def select_file_to_save():
    return filedialog.asksaveasfilename()
