* Layouts
  * ScrollView (complete)
    * horizontal_scroll: bool
    * vertical_scroll: bool
    * wrap_horizontal: bool
    * wrap_vertical: bool
    * scroll_thickness: int
  * Column
    * expand_horizontal: bool
    * TODO: horizontal alignment
  * Row
    * expand_vertical: bool
    * TODO: vertical alignment
  * View (complete)
    * control: Widget
    * width: int
    * height: int
  * RadioGroup
    * content: Widget
    * value: Optional[Any]
    * on_change: Callback[[RadioGroup], None]
    * can_deselect: bool = False
* Widgets
  * Rectangle (complete)
    * width: int
    * height: int
    * coloring: Gradient
  * Button: AbstractButton
    * text: str
    * on_click: Callable[[Button], None]
  * Checkbox: AbstractButton
    * checked: bool = False
    * on_change: Callable[[Checkbox], None]
  * Radio: AbstractButton
    * value: Any
  * Text
    * text: str
  * Label:
    * for_button: AbstractButton | str  # key
