import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.effects.scroll import ScrollEffect
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from pysaurus.interface.kivysaurus.set_input import SetInput


class SensitiveLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.count = 0

    def update_text(self, delay):
        print("Updating text", delay)
        self.count += 1
        self.text = f"Touched {self.count} time(s)."
        if self.count == 100:
            return False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            Clock.schedule_interval(self.update_text, 2)
            return True
        return super().on_touch_down(touch)


def resize(*args):
    print("Resized", args)


class KivySaurus(App):
    def build(self):
        set_input = SetInput(int, [1, 2, 5, 4], size_hint=(1, None))
        set_input.bind(minimum_height=set_input.setter("height"))
        view = ScrollView(
            size_hint=(1, None),
            size=(Window.width, Window.height),
            effect_cls=ScrollEffect,
        )
        Window.bind(size=view.setter('size'))
        view.add_widget(set_input)
        return view


if __name__ == "__main__":
    kivy.require("2.1.0")
    KivySaurus().run()
