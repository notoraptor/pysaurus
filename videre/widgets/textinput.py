import bisect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import pygame
import pygame.gfxdraw

from pysaurus.core.stringsplit import get_next_word_position, get_previous_word_position
from videre.colors import Colors
from videre.core.events import KeyboardEntry, MouseEvent
from videre.core.fontfactory.pygame_text_rendering import RenderedText
from videre.core.mouse_ownership import MouseOwnership
from videre.layouts.abstractlayout import AbstractLayout
from videre.layouts.container import Container
from videre.widgets.text import Text
from videre.widgets.widget import Widget


@dataclass(slots=True)
class _SelectionDefinition:
    start: int
    end: int


@dataclass(slots=True)
class _CursorDefinition:
    x: int
    y: int
    pos: int


class _CursorEvent(ABC):
    @abstractmethod
    def handle(self, rendered: RenderedText) -> _CursorDefinition:
        raise NotImplementedError()

    @classmethod
    def null(self, rendered: RenderedText) -> _CursorDefinition:
        x = 0
        y = rendered.font_sizes.height_delta
        pos = 0
        return _CursorDefinition(x, y, pos)


class _CursorMouseEvent(_CursorEvent):
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"{type(self).__name__}({self.x}, {self.y})"

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.x == other.x and self.y == other.y

    def handle(self, rendered: RenderedText) -> _CursorDefinition:
        x = self.x
        y = self.y

        lines = rendered.lines
        if not lines:
            return self.null(rendered)

        ys = [line.y for line in lines]
        line_pos = max(0, bisect.bisect_right(ys, y) - 1)
        line = lines[line_pos]
        if not line.elements:
            return self.null(rendered)

        xs = [el.x for el in line.elements]
        word_pos = max(0, bisect.bisect_right(xs, x) - 1)
        word = line.elements[word_pos]
        char_xs = [word.x + ch.x for ch in word.tasks]
        char_pos = max(0, bisect.bisect_right(char_xs, x) - 1)
        char = word.tasks[char_pos]
        left = char.x
        right = char.x + char.horizontal_shift

        cursor_y = line.y - rendered.font_sizes.ascender
        if x - left < right - x:
            cursor_x = left
            chosen_charpos = char.pos
        else:
            cursor_x = right
            chosen_charpos = char.pos + 1

        # print(char.x, char.el, "left" if cursor_x == left else "right")
        return _CursorDefinition(x=cursor_x, y=cursor_y, pos=chosen_charpos)


class _CursorCharPosEvent(_CursorEvent):
    def __init__(self, pos: int):
        self.pos = pos

    def __repr__(self):
        return f"{type(self).__name__}({self.pos})"

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.pos == other.pos

    def handle(self, rendered: RenderedText) -> _CursorDefinition:
        pos = self.pos

        lines = rendered.lines
        if not lines:
            return self.null(rendered)

        line_pos = max(
            0,
            bisect.bisect_right(
                lines, pos, key=lambda line: line.elements[0].tasks[0].pos
            )
            - 1,
        )
        line = lines[line_pos]
        if not line.elements:
            return self.null(rendered)

        word_pos = max(
            0, bisect.bisect_right(line.elements, pos, key=lambda w: w.tasks[0].pos) - 1
        )
        word = line.elements[word_pos]
        char_pos = max(
            0, bisect.bisect_right(word.tasks, pos, key=lambda chr: chr.pos) - 1
        )
        char = word.tasks[char_pos]

        left = char.x
        right = char.x + char.horizontal_shift

        cursor_y = line.y - rendered.font_sizes.ascender
        if pos > char.pos:
            cursor_x = right
        else:
            cursor_x = left
        return _CursorDefinition(x=cursor_x, y=cursor_y, pos=pos)


class _InputText(Text):
    __wprops__ = {}
    __slots__ = ()


class TextInput(AbstractLayout):
    __wprops__ = {"has_focus"}
    __slots__ = (
        "_text",
        "_container",
        "_cursor_event",
        "_char_position",
        "_selection",
        "_is_selecting",
    )
    __size__ = 1
    __capture_mouse__ = True

    def __init__(self, **kwargs):
        self._text = _InputText(text="Hello, 炎炎ノ消防隊: ", size=80)
        self._container = Container(self._text, background_color=Colors.white)
        super().__init__([self._container], **kwargs)
        self._cursor_event: Optional[_CursorEvent] = None
        self._char_position = 0
        self._selection: Optional[_SelectionDefinition] = None
        self._is_selecting = False
        self._set_focus(False)
        self._set_char_pos(len(self._text.text))

    @property
    def _control(self) -> Widget:
        (control,) = self._controls()
        return control

    def _has_focus(self) -> bool:
        return self._get_wprop("has_focus")

    def _set_focus(self, value):
        self._set_wprop("has_focus", bool(value))

    def _char_pos(self) -> int:
        return self._char_position

    def _set_char_pos(self, pos: int):
        self._char_position = pos

    def get_mouse_owner(
        self, x_in_parent: int, y_in_parent: int
    ) -> Optional[MouseOwnership]:
        return Widget.get_mouse_owner(self, x_in_parent, y_in_parent)

    def handle_mouse_down(self, event: MouseEvent):
        self._debug("mouse_down")
        self._is_selecting = True
        self._selection = None
        self._set_cursor_event(_CursorMouseEvent(event.x, event.y))

    def handle_mouse_up(self, event: MouseEvent):
        self._debug("mouse_up")
        self._is_selecting = False

    def handle_mouse_down_move(self, event: MouseEvent):
        if self._is_selecting:
            self._debug("mouse_down_move")
            self._set_cursor_event(_CursorMouseEvent(event.x, event.y))

    def handle_focus_in(self) -> bool:
        self._debug("focus_in")
        self._set_focus(True)
        if not self._cursor_event:
            self._cursor_event = _CursorCharPosEvent(0)
        return True

    def handle_focus_out(self):
        self._debug("focus_out")
        self._set_focus(False)
        self._selection = None

    def handle_text_input(self, text: str):
        self._debug("text_input", repr(text))
        if self._selection:
            # Replace selected text
            start, end = self._selection.start, self._selection.end
            in_text = self._text.text
            out_text = in_text[:start] + text + in_text[end:]
            self._text.text = out_text
            self._set_char_pos(start + len(text))
            self._selection = None
        else:
            # Normal insertion
            in_text = self._text.text
            in_pos = self._char_pos()
            out_text = in_text[:in_pos] + text + in_text[in_pos:]
            out_pos = in_pos + len(text)
            self._text.text = out_text
            self._set_char_pos(out_pos)
        self._set_cursor_event(_CursorCharPosEvent(self._char_pos()))

    def handle_keydown(self, key: KeyboardEntry):
        self._debug("key_down")
        if key.backspace:
            if self._selection:
                # Delete selected text
                start, end = self._selection.start, self._selection.end
                in_text = self._text.text
                out_text = in_text[:start] + in_text[end:]
                self._text.text = out_text
                self._set_char_pos(start)
                self._selection = None
            else:
                # Normal backspace
                in_text = self._text.text
                in_pos = self._char_pos()
                out_pos = max(0, in_pos - 1)
                out_text = in_text[:out_pos] + in_text[in_pos:]
                self._text.text = out_text
                self._set_char_pos(out_pos)
            self._set_cursor_event(_CursorCharPosEvent(self._char_pos()))
        elif key.left:
            in_pos = self._char_pos()
            select_start = False
            if not key.shift:
                if self._selection:
                    # We get out of selection.
                    # If we move through chars, we should not move.
                    # If we move through words, we should move.
                    if not key.ctrl:
                        in_pos += 1
                self._selection = None
            elif not self._selection:
                # Start selection
                self._selection = _SelectionDefinition(in_pos, in_pos)
                select_start = True
            else:
                assert in_pos in (self._selection.start, self._selection.end)
                select_start = in_pos == self._selection.start
            if key.ctrl:
                out_pos = get_previous_word_position(self._text.text, in_pos - 1)
            else:
                out_pos = max(0, in_pos - 1)
            self._set_char_pos(out_pos)
            if key.shift and self._selection:
                # Update selection
                if select_start:
                    self._selection.start = out_pos
                else:
                    self._selection.end = out_pos
            self._set_cursor_event(_CursorCharPosEvent(out_pos))
        elif key.right:
            in_pos = self._char_pos()
            select_start = False
            if not key.shift:
                if self._selection:
                    # We get out of selection.
                    # If we move through chars, we should not move.
                    # If we move through words, we should move.
                    if not key.ctrl:
                        in_pos -= 1
                self._selection = None
            elif not self._selection:
                # Start selection
                self._selection = _SelectionDefinition(in_pos, in_pos)
            else:
                assert in_pos in (self._selection.start, self._selection.end)
                select_start = in_pos == self._selection.start
            if key.ctrl:
                out_pos = get_next_word_position(self._text.text, in_pos)
            else:
                out_pos = min(in_pos + 1, len(self._text.text))
            self._set_char_pos(out_pos)
            if key.shift and self._selection:
                # Update selection
                if select_start:
                    self._selection.start = out_pos
                else:
                    self._selection.end = out_pos
            self._set_cursor_event(_CursorCharPosEvent(out_pos))
        elif key.ctrl:
            if key.a:
                # Select all
                self._selection = _SelectionDefinition(0, len(self._text.text))
                self._set_char_pos(len(self._text.text))
                self._set_cursor_event(_CursorCharPosEvent(self._char_pos()))
            elif key.c and self._selection:
                content = self._text.text[self._selection.start : self._selection.end]
                self.get_window().set_clipboard(content)
                self._debug("copied", repr(content))
            elif key.v:
                inserted = self.get_window().get_clipboard()
                if inserted:
                    in_text = self._text.text
                    if self._selection:
                        start, end = self._selection.start, self._selection.end
                        out_text = in_text[:start] + inserted + in_text[end:]
                        self._text.text = out_text
                        self._set_char_pos(start + len(inserted))
                        self._selection = None
                    else:
                        in_pos = self._char_pos()
                        out_text = in_text[:in_pos] + inserted + in_text[in_pos:]
                        self._text.text = out_text
                        self._set_char_pos(in_pos + len(inserted))
                    self._set_cursor_event(_CursorCharPosEvent(self._char_pos()))

    def _set_cursor_event(self, event: _CursorEvent):
        if self._cursor_event:
            assert type(self._cursor_event) is type(event), (
                f"Unexpected different consecutive cursor event types: "
                f"{self._cursor_event}, {event}"
            )
        if self._cursor_event != event:
            self._cursor_event = event
            self.update()

    @classmethod
    def _get_cursor_rect(cls, cursor: _CursorDefinition, rendered: RenderedText):
        cursor_width = 2
        cursor_height = rendered.font_sizes.ascender + rendered.font_sizes.descender
        return pygame.Rect(cursor.x, cursor.y, cursor_width, cursor_height)

    def _get_selection_rects(self, rendered: RenderedText) -> list[pygame.Rect]:
        if not self._selection:
            return []

        start, end = self._selection.start, self._selection.end
        if start > end:
            start, end = end, start

        rects = []
        for line in rendered.lines:
            if not line.elements:
                continue

            line_start = line.elements[0].tasks[0].pos
            line_end = line.elements[-1].tasks[-1].pos + 1

            if line_end <= start or line_start >= end:
                continue

            # Calculate x coordinates for this line
            if line_start < start:
                start_x = None
                for word in line.elements:
                    for char in word.tasks:
                        if char.pos >= start:
                            start_x = word.x + char.x
                            break
                    if start_x is not None:
                        break
                assert start_x is not None
            else:
                start_x = line.elements[0].x

            if line_end > end:
                end_x = None
                for word in line.elements:
                    for char in word.tasks:
                        if char.pos >= end:
                            end_x = word.x + char.x
                            break
                    if end_x is not None:
                        break
                assert end_x is not None
            else:
                end_x = line.elements[-1].x + line.elements[-1].width

            print(
                "sel pos",
                start,
                end,
                "line pos",
                line_start,
                line_end,
                "coords",
                start_x,
                end_x,
                "limit",
                line.limit(),
            )
            # Create selection rectangle for this line
            rect = pygame.Rect(
                start_x,
                line.y - rendered.font_sizes.ascender,
                end_x - start_x,
                rendered.font_sizes.ascender + rendered.font_sizes.descender,
            )
            rects.append(rect)

        return rects

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        text_surface = self._control.render(window, width, height)
        rendered = self._text._rendered
        surface = text_surface.copy()

        # Draw selection if any
        if self._selection:
            selection_rects = self._get_selection_rects(rendered)
            for rect in selection_rects:
                pygame.gfxdraw.box(surface, rect, (100, 100, 255, 100))

        # Draw cursor if focused
        if self._has_focus() and self._cursor_event:
            cursor_def = self._cursor_event.handle(rendered)
            cursor = self._get_cursor_rect(cursor_def, rendered)
            pygame.gfxdraw.box(surface, cursor, Colors.black)
            self._set_char_pos(cursor_def.pos)
        # Reset cursor event after drawing
        self._cursor_event = None

        return surface
