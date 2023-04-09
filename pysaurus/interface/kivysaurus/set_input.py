from typing import Callable, Sequence, Type, Union

from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from pysaurus.core.functions import identity
from pysaurus.interface.kivysaurus.kivy_utils import alert

Types = Union[Type, Sequence[Type]]
ValueType = Type[Union[str, bool, int, float]]


class TypeValidator:
    __slots__ = "types", "wrapper", "parser"

    def __init__(self, types: Types, wrapper: Callable = None, parser: Callable = None):
        self.types = types
        self.wrapper = wrapper
        self.parser = parser or (
            self.types if isinstance(self.types, type) else identity
        )

    def __call__(self, value):
        assert isinstance(value, self.types)
        return value if self.wrapper is None else self.wrapper(value)


def parse_bool(value: str):
    return value.lower() not in ("false", "0")


TYPE_VALIDATORS = {
    str: TypeValidator(str),
    bool: TypeValidator(bool, parser=parse_bool),
    int: TypeValidator(int),
    float: TypeValidator((bool, int, float), float),
}

SIZE_HINT = (1, None)


class ValueButton(Button):
    value = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(size_hint=SIZE_HINT, **kwargs)


class SetInput(GridLayout):
    values = ListProperty()

    def __init__(self, value_type: ValueType, initial_values: list, **kwargs):
        validator = TYPE_VALIDATORS[value_type]
        values = sorted({validator(value) for value in initial_values})
        super().__init__(values=values, cols=2, **kwargs)
        self.value_type = value_type
        self.text_input = TextInput(
            multiline=False, text_validate_unfocus=False, size_hint=SIZE_HINT
        )
        self.add_button = Button(text="+", size_hint=SIZE_HINT)
        self.text_input.bind(on_text_validate=self.add_value)
        self.add_button.bind(on_press=self.add_value)
        self._draw()

    def _draw(self):
        self.clear_widgets()
        for value in self.values:
            button = ValueButton(value=value, text="-")
            button.bind(on_press=self.remove_value)
            self.add_widget(Label(text=str(value), size_hint=SIZE_HINT))
            self.add_widget(button)
        self.add_widget(self.text_input)
        self.add_widget(self.add_button)

    def remove_value(self, button: ValueButton):
        validator = TYPE_VALIDATORS[self.value_type]
        value = validator(button.value)
        current_values = set(self.values)
        if value in current_values:
            current_values.remove(value)
            self.values = sorted(current_values)
            self._draw()

    def add_value(self, *args):
        text = self.text_input.text.strip()
        if text:
            self.text_input.text = ""
            parser = TYPE_VALIDATORS[self.value_type].parser
            try:
                value = parser(text)
                current_values = set(self.values)
                if value not in current_values:
                    current_values.add(value)
                    self.values = sorted(current_values)
                    self._draw()
            except Exception as exc:
                alert(exc)
