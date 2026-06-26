"""Properties page — custom property management (phase 0 placeholder)."""

from videre import Text
from videre.widgets.widget import Widget

from pysaurus.interface.videroid.pages.base_page import Page


class PropertiesPage(Page):
    title = "Properties"

    def build(self) -> Widget:
        return Text("Properties — to implement (phase 6)")
