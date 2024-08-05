from videre.widgets.widget import Widget


class Procedure:
    __slots__ = ("proc",)

    def __init__(self, procedure: callable):
        self.proc = procedure

    def __call__(self, widget: Widget):
        return self.proc()


class WidgetSet:
    __slots__ = ("_widget", "_props")

    def __init__(self, widget, **props):
        self._widget = widget
        self._props = props

    def __call__(self, clicked: Widget):
        widget = self._widget
        for name, value in self._props.items():
            setattr(widget, name, value)
