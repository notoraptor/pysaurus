"""Files page — non-video file inventory & video stats (phase 0 placeholder)."""

from videre import Text
from videre.widgets.widget import Widget

from pysaurus.interface.videroid.pages.base_page import Page


class FilesPage(Page):
    title = "Files"

    def build(self) -> Widget:
        return Text("Files — to implement (phase 7)")
