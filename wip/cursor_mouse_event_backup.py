from videre.core.fontfactory.pygame_text_rendering import RenderedText
from videre.widgets.textinput.textinput import _CursorDefinition, _CursorMouseEvent


class _CursorMouseEventBackup(_CursorMouseEvent):
    def handle(self, rendered: RenderedText) -> _CursorDefinition:
        output = self._handle(rendered)
        if output is None:
            return self.null(rendered)
        line, chosen_charpos, left, right, to_right = output
        cursor_x = right if to_right else left
        cursor_y = line.y - rendered.font_sizes.ascender
        return _CursorDefinition(x=cursor_x, y=cursor_y, pos=chosen_charpos)
