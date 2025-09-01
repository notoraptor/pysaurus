import videre
from videre.widgets.widget import Widget

from pysaurus.core.notifications import Notification
from pysaurus.core.profiling import Profiler
from pysaurus.interface.api.gui_api import GuiAPI
from pysaurus.video.video_pattern import VideoPattern


class _VidereGuiAPI(GuiAPI):
    __slots__ = ("window",)

    def __init__(self, window: videre.Window) -> None:
        super().__init__()
        self.window = window

    def _notify(self, notification: Notification) -> None:
        self.window.notify(notification)


class PysaurusBackend:
    def __init__(self, window: videre.Window) -> None:
        window.data = self

        self.__api = _VidereGuiAPI(window)
        self.get_constants = self.__api.get_constants
        self.get_database_names = self.__api.application.get_database_names
        self.open_database = self.__api.open_database
        self.close_app = self.__api.close_app
        self.get_python_backend = Profiler.profile()(self.__api.get_python_backend)
        self.open_from_server = self.__api.open_from_server

    def get_video(self, video_id: int) -> VideoPattern:
        (video,) = self.__api.database.get_videos(where={"video_id": video_id})
        return video

    def open_video(self, video_id: int):
        self.__api.database.open_video(video_id)

    def open_containing_folder(self, video_id: int) -> str:
        return self.__api.open_containing_folder(video_id)

    def mark_as_read(self, video_id: int) -> bool:
        return self.__api.database.mark_as_read(video_id)


def get_backend(widget: Widget) -> PysaurusBackend:
    data = widget.get_window().data
    assert isinstance(data, PysaurusBackend)
    return data
