import videre
from pysaurus.interface.using_videre.video_view import VideoView
from pysaurus.video.database_context import DatabaseContext


class VideosPage(videre.Column):
    __wprops__ = {}
    __slots__ = ("context",)

    def __init__(self, context: DatabaseContext):
        videos_view = videre.Column(
            [VideoView(video, i) for i, video in enumerate(context.view.result)]
        )

        left_bar = videre.Text("view parameters", weight=1)
        right_view = videre.ScrollView(videos_view, wrap_horizontal=True, weight=4)

        top_bar = videre.Text(f"Database: {context.name}")
        center_bar = videre.Row([left_bar, right_view], weight=1)
        bottom_bar = videre.Text("bottom bar")

        super().__init__([top_bar, center_bar, bottom_bar])
        self.context = context
