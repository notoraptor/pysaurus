import dataclasses
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Self, Union

from videre import Alignment, Border, Colors
from videre.core.constants import MouseButton
from videre.core.events import MouseEvent
from videre.core.sides.padding import Padding
from videre.gradient import ColoringDefinition
from videre.layouts.container import Container
from videre.layouts.control_layout import ControlLayout
from videre.widgets.widget import Widget


@dataclass(slots=True)
class Style:
    border: Border = None
    padding: Padding = None
    background_color: ColoringDefinition = None
    vertical_alignment: Alignment = None
    horizontal_alignment: Alignment = None
    width: int = None
    height: int = None

    def fill_with(self, other: "Style"):
        if self.border is None:
            self.border = other.border
        if self.padding is None:
            self.padding = other.padding
        if self.background_color is None:
            self.background_color = other.background_color
        if self.vertical_alignment is None:
            self.vertical_alignment = other.vertical_alignment
        if self.horizontal_alignment is None:
            self.horizontal_alignment = other.horizontal_alignment
        if self.width is None:
            self.width = other.width
        if self.height is None:
            self.height = other.height

    def get_specific_from(self, other: "Style"):
        return Style(
            **{
                key: value
                for key, value in self.to_dict().items()
                if value != getattr(other, key)
            }
        )

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclass(slots=True)
class StyleDef:
    default: Style = dataclasses.field(default_factory=Style)
    hover: Optional[Style] = None
    click: Optional[Style] = None

    def __post_init__(self):
        if self.hover is None:
            self.hover = dataclasses.replace(self.default)
        else:
            self.hover.fill_with(self.default)
        if self.click is None:
            self.click = dataclasses.replace(self.default)
        else:
            self.click.fill_with(self.default)

    def merged_with(self, style: "StyleType") -> Self:
        base_style = self
        if style is None:
            return base_style
        else:
            output = {
                "default": dataclasses.replace(base_style.default),
                "hover": base_style.hover.get_specific_from(base_style.default),
                "click": base_style.click.get_specific_from(base_style.default),
            }
            if isinstance(style, StyleDef):
                for key in ("default", "hover", "click"):
                    if getattr(style, key) is not None:
                        output_key = dataclasses.replace(getattr(style, key))
                        output_key.fill_with(output[key])
                        output[key] = output_key
            elif isinstance(style, dict):
                for key in ("default", "hover", "click"):
                    if key in style:
                        output_key = Style(**style[key])
                        output_key.fill_with(output[key])
                        output[key] = output_key
            else:
                raise TypeError(f"Invalid style type {type(style)}")
            return StyleDef(**output)


StyleType = Optional[Union[StyleDef, Dict[str, Dict[str, Any]]]]
OnClickType = Optional[Callable[[Widget], None]]


class Div(ControlLayout):
    __slots__ = ("_hover", "_down", "_style", "_on_click")
    __wprops__ = {}
    __capture_mouse__ = True
    __style__: StyleDef = StyleDef(
        default=Style(
            padding=Padding.axis(horizontal=6, vertical=4),
            border=Border.all(1),
            vertical_alignment=Alignment.CENTER,
            horizontal_alignment=Alignment.CENTER,
        ),
        hover=Style(background_color=Colors.lightgray),
        click=Style(background_color=Colors.gray),
    )

    def __init__(
        self,
        control: Optional[Widget] = None,
        style: StyleType = None,
        on_click: OnClickType = None,
        **kwargs,
    ):
        style = self.__style__.merged_with(style)
        super().__init__(Container(control, **style.default.to_dict()), **kwargs)
        self._hover = False
        self._down = False
        self._style = style
        self._on_click = on_click

    def _container(self) -> Container:
        (container,) = self._controls()
        return container

    def handle_mouse_enter(self, event: MouseEvent):
        self._hover = True
        self._set_style()

    def handle_mouse_exit(self):
        self._hover = False
        self._set_style()

    def handle_mouse_down(self, event: MouseEvent):
        self._down = True
        self._set_style()

    def handle_mouse_up(self, event: MouseEvent):
        return self.handle_mouse_down_canceled(event.button)

    def handle_mouse_down_canceled(self, button: MouseButton):
        self._down = False
        self._set_style()

    def handle_click(self, button: MouseButton):
        if self._on_click is not None:
            self._on_click(self)

    def _set_style(self):
        if self._down:
            style = self._style.click
        elif self._hover:
            style = self._style.hover
        else:
            style = self._style.default
        (container,) = self._controls()
        for key, value in style.to_dict().items():
            setattr(container, key, value)
