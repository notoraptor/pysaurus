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
* Widgets
  * Rectangle (complete)
    * width: int
    * height: int
    * coloring: Gradient
  * Button
    * text: str
    * on_click: Callable[[Button], None]
  * Checkbox
    * checked: bool = False
    * on_change: Callable[[Checkbox], None]
  * Text
    * text: str
