import sys
import traceback

from kivy.uix.label import Label
from kivy.uix.popup import Popup


def alert(exception: Exception):
    traceback.print_tb(exception.__traceback__)
    print(type(exception), exception, file=sys.stderr)
    popup = Popup(
        title="Error", content=Label(text=str(exception)), size_hint=(0.6, 0.6)
    )
    popup.open()
