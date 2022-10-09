from typing import Optional

from pysaurus.core.functions import camel_case_to_snake_case
from pysaurus.core.notifications import Notification


class JobToDo(Notification):
    __slots__ = "name", "total", "title"

    def __init__(self, name: str, total: int, title: str = None):
        self.name = name
        self.total = total
        self.title = title


class JobStep(Notification):
    __slots__ = "name", "channel", "step", "total", "title"
    __slot_sorter__ = list

    def __init__(
        self,
        name: str,
        channel: Optional[str],
        step: int,
        total: int,
        *,
        title: str = None,
    ):
        self.name = name
        self.channel = channel
        self.step = step
        self.total = total
        self.title = title


class JobNotifications:
    __slots__ = "name", "notifier"
    __kind__ = "datas"

    def __init__(self, total: int, notifier, title: str = None, pretty_total=None):
        name = camel_case_to_snake_case(type(self).__name__).replace("_", " ")
        if title is None:
            if pretty_total is None:
                pretty_total = f"{total} {self.__kind__}"
            title = f"{name} ({pretty_total})"
        self.name = name
        self.notifier = notifier
        self.notifier.notify(JobToDo(self.name, total, title))
        if total:
            self.notifier.notify(JobStep(self.name, None, 0, total, title=title))

    def progress(
        self,
        channel: Optional[str],
        channel_step: int,
        channel_size: int,
        *,
        title: str = None,
    ):
        self.notifier.notify(
            JobStep(self.name, channel, channel_step, channel_size, title=title)
        )


class CollectVideosFromFolders(JobNotifications):
    __slots__ = ()
    __kind__ = "folders"


class CollectVideoInfos(JobNotifications):
    __slots__ = ()
    __kind__ = "videos"


class CollectVideoStreamLanguages(JobNotifications):
    __slots__ = ()
    __kind__ = "stream languages"


class CollectVideoThumbnails(JobNotifications):
    __slots__ = ()
    __kind__ = "videos"


class CompressThumbnailsToJpeg(JobNotifications):
    __slots__ = ()
    __kind__ = "PNG thumbnails"


class CollectVideoMiniatures(JobNotifications):
    __slots__ = ()
    __kind__ = "videos"


class CollectMiniatureGroups(JobNotifications):
    __slots__ = ()
    __kind__ = "miniatures"


class CompareMiniatureGrays(JobNotifications):
    __slots__ = ()
    __kind__ = "miniatures"


class CompareOldVsNewMiniatures(JobNotifications):
    __slots__ = ()
    __kind__ = "new miniatures"


class CompareMiniatures(JobNotifications):
    __slots__ = ()
    __kind__ = "videos (C++ comparison)"


class CompareMiniaturesFromPython(JobNotifications):
    __slots__ = ()
    __kind__ = "videos (Python comparison)"


class LinkComparedMiniatures(JobNotifications):
    __slots__ = ()
    __kind__ = "positions"


class LinkComparedVideos(JobNotifications):
    __slots__ = ()
    __kind__ = "videos"


class CopyFile(JobNotifications):
    __slots__ = ()
    __kind__ = "bytes"


class OptimizePatternPredictor(JobNotifications):
    __slots__ = ()
    __kind__ = "steps"


class PredictPattern(JobNotifications):
    __slots__ = ()
    __kind__ = "videos"
