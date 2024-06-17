import pygame

from other.pyguisaurus.widget import Widget


class ScrollView(Widget):
    __attributes__ = {"control", "scroll_thickness"}
    __slots__ = ()
    _SCROLL_COLOR = pygame.Color(216, 216, 216)

    def __init__(self, control: Widget, scroll_thickness=18, **kwargs):
        super().__init__(**kwargs)
        self._set_attribute("control", control)
        self._set_attribute("scroll_thickness", scroll_thickness)

    @property
    def control(self) -> Widget:
        return self._get_attribute("control")

    @property
    def scroll_thickness(self) -> int:
        return self._get_attribute("scroll_thickness")

    def draw(self, window, width: int = None, height: int = None) -> pygame.Surface:
        content = self.control.render(window, None, None)
        content_width, content_height = content.get_width(), content.get_height()
        if width is None:
            width = content_width
        if height is None:
            height = content_height
        print((width, height), (content_width, content_height))

        if width == content_width and height == content_height:
            return content

        view = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        view.blit(content, (0, 0))
        scroll_thickness = self.scroll_thickness
        if content_width > width:
            h_scroll_width = (width * width) // content_width
            horizontal_scroll = pygame.Surface((h_scroll_width, scroll_thickness))
            horizontal_scroll.fill(self._SCROLL_COLOR)
            view.blit(horizontal_scroll, (0, height - scroll_thickness))
            print((0, height - scroll_thickness), (h_scroll_width, scroll_thickness))
        if content_height > height:
            v_scroll_height = (height * height) // content_height
            vertical_scroll = pygame.Surface((scroll_thickness, v_scroll_height))
            vertical_scroll.fill(self._SCROLL_COLOR)
            view.blit(vertical_scroll, (width - scroll_thickness, 0))
        return view
