import pygame

from other.pyguisaurus.container import Container
from other.pyguisaurus.widget import Widget


class ScrollView(Container):
    __attributes__ = {
        "scroll_thickness",
        "horizontal_scroll",
        "vertical_scroll",
        "expand_children_horizontal",
        "expand_children_vertical",
    }
    __size__ = 1
    __slots__ = ("_content_x", "_content_y")
    _SCROLL_COLOR = pygame.Color(216, 216, 216)
    _SCROLL_STEP = 120

    def __init__(
        self,
        control: Widget,
        scroll_thickness=18,
        horizontal_scroll=True,
        vertical_scroll=True,
        expand_children_horizontal=False,
        expand_children_vertical=False,
        **kwargs
    ):
        super().__init__([control], **kwargs)
        self._set_attribute("scroll_thickness", scroll_thickness)
        self._set_attribute("horizontal_scroll", horizontal_scroll)
        self._set_attribute("vertical_scroll", vertical_scroll)
        self._set_attribute("expand_children_horizontal", expand_children_horizontal)
        self._set_attribute("expand_children_vertical", expand_children_vertical)
        self._content_x = 0
        self._content_y = 0

    @property
    def control(self) -> Widget:
        (control,) = self._controls()
        return control

    @property
    def scroll_thickness(self) -> int:
        return self._get_attribute("scroll_thickness")

    @property
    def horizontal_scroll(self) -> bool:
        return self._get_attribute("horizontal_scroll")

    @property
    def vertical_scroll(self) -> bool:
        return self._get_attribute("vertical_scroll")

    @property
    def expand_children_horizontal(self) -> bool:
        return self._get_attribute("expand_children_horizontal")

    @property
    def expand_children_vertical(self) -> bool:
        return self._get_attribute("expand_children_vertical")

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        c_w_hint = width if self.expand_children_horizontal else None
        c_h_hint = height if self.expand_children_vertical else None
        content = self.control.render(window, c_w_hint, c_h_hint)
        content_w, content_h = content.get_width(), content.get_height()
        if width is None:
            width = content_w
        if height is None:
            height = content_h

        if (
            width == content_w
            and height == content_h
            and self._content_x == 0
            and self._content_y == 0
        ):
            return content

        if content_w <= width:
            self._content_x = 0
        elif self._content_x > 0:
            self._content_x = 0
        elif self._content_x + content_w < width - 1:
            self._content_x = width - content_w

        if content_h <= height:
            self._content_y = 0
        elif self._content_y > 0:
            self._content_y = 0
        elif self._content_y + content_h < height - 1:
            self._content_y = height - content_h

        h_scroll = None
        v_scroll = None
        scroll_thickness = self.scroll_thickness

        if content_w > width and self.horizontal_scroll:
            h_scroll_width = (width * width) // content_w
            h_scroll = pygame.Surface((h_scroll_width, scroll_thickness))
            h_scroll.fill(self._SCROLL_COLOR)
            if "h" in self._transient_state:
                step = self._SCROLL_STEP * self._transient_state["h"]
                if step > 0:
                    # scroll left
                    self._content_x = min(self._content_x + step, 0)
                else:
                    # scroll right
                    self._content_x = max(self._content_x + step, width - content_w)

        if content_h > height and self.vertical_scroll:
            v_scroll_height = (height * height) // content_h
            v_scroll = pygame.Surface((scroll_thickness, v_scroll_height))
            v_scroll.fill(self._SCROLL_COLOR)
            if "v" in self._transient_state:
                step = self._SCROLL_STEP * self._transient_state["v"]
                if step > 0:
                    # scroll top (show topper content)
                    self._content_y = min(self._content_y + step, 0)
                else:
                    # scroll bottom (show most bottom content)
                    self._content_y = max(self._content_y + step, height - content_h)

        print(
            (width, height), (self._content_x, self._content_y), (content_w, content_h)
        )

        view = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        view.blit(content, (self._content_x, self._content_y))
        if h_scroll:
            h_scroll_x = (abs(self._content_x) * width) // content_w
            view.blit(h_scroll, (h_scroll_x, height - scroll_thickness))
        if v_scroll:
            v_scroll_y = (abs(self._content_y) * height) // content_h
            view.blit(v_scroll, (width - scroll_thickness, v_scroll_y))
        return view

    def get_mouse_wheel_owner(self, x: int, y: int):
        if Widget.get_mouse_owner(self, x, y):
            child = self.get_mouse_owner(x, y)
            if isinstance(child, ScrollView):
                return child
            else:
                return self
        return None

    def _can_scroll_horizontal(self, direction) -> bool:
        if not self.horizontal_scroll or not direction:
            return False
        if direction > 0:
            # scroll left
            return self._content_x < 0
        else:
            # scroll right
            return self._content_x > self.rendered_width - self.control.rendered_width

    def _can_scroll_vertical(self, direction) -> bool:
        if not self.vertical_scroll or not direction:
            return False
        if direction > 0:
            # scroll top
            return self._content_y < 0
        else:
            # scroll bottom
            return self._content_y > self.rendered_height - self.control.rendered_height

    def handle_mouse_wheel(self, x: int, y: int, shift: bool):
        if not x and not y:
            return

        horizontal, vertical = 0, 0
        if x and y:
            horizontal, vertical = x, y
        elif x:
            horizontal = x
        elif shift:
            horizontal = y
        else:
            vertical = y

        if self._can_scroll_horizontal(horizontal):
            self._transient_state["h"] = horizontal
        if self._can_scroll_vertical(vertical):
            self._transient_state["v"] = vertical
