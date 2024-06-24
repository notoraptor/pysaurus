class MouseOwnership:
    """
    Represent a mouse ownership.
    widget: widget that owns mouse.
    rel_x, rel_y: mouse coordinates relative to widget parent.
    """

    __slots__ = ("widget", "rel_x", "rel_y")

    def __init__(self, widget, rel_x: int, rel_y: int):
        from other.pyguisaurus.widgets.widget import Widget

        self.widget: Widget = widget
        self.rel_x = rel_x
        self.rel_y = rel_y
