from abc import abstractmethod

from pysaurus.core.database.video import Video
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.functions import camel_case_to_snake_case


class AbstractSourceNode:
    __slots__ = ()

    @abstractmethod
    def database(self):
        raise NotImplementedError()

    @abstractmethod
    def parent(self):
        raise NotImplementedError()

    @abstractmethod
    def videos(self):
        raise NotImplementedError()

    def count(self):
        return sum(1 for _ in self.videos())

    @classmethod
    def get_name(cls):
        return cls.__title__ if hasattr(cls, '__title__') else camel_case_to_snake_case(cls.__name__)

    def __str__(self):
        chain = []
        parent = self
        while True:
            new_parent = parent.parent()
            chain.append(parent)
            if new_parent:
                parent = new_parent
            else:
                break
        path_name = '.'.join(camel_case_to_snake_case(type(element).get_name()) for element in reversed(chain))
        return '%s/%d' % (path_name, self.count())

    def __len__(self):
        return self.count()

    def __iter__(self):
        return self.videos()


class SourceNode(AbstractSourceNode):
    __slots__ = ('__parent', '__database')

    def __init__(self, parent):
        self.__parent = parent  # type: SourceNode
        self.__database = self.__parent.database()

    def parent(self):
        return self.__parent

    def database(self):
        return self.__parent.database()

    def videos(self):
        return (video for video in self.__parent.videos() if self.filter(self.__database, video))

    @abstractmethod
    def filter(self, database, video: VideoState):
        raise NotImplementedError()


class NotFound(SourceNode):
    __slots__ = ()

    def filter(self, database, video: VideoState):
        return not video.exists()


class Found(SourceNode):
    __slots__ = ()

    def filter(self, database, video: VideoState):
        return video.exists()


class WithThumbnails(SourceNode):
    __slots__ = ()

    def filter(self, database, video: Video):
        return video.thumbnail_is_valid()


class WithoutThumbnails(SourceNode):
    __slots__ = ()

    def filter(self, database, video: Video):
        return not video.thumbnail_is_valid()


class VideoSource(AbstractSourceNode):
    __slots__ = ('__database', '__source')

    def __init__(self, database, source: dict):
        self.__database = database
        self.__source = source

    def database(self):
        return self.__database

    def parent(self):
        return None

    def videos(self):
        return iter(self.__source.values())


class ReadableFound(Found):
    __slots__ = ('with_thumbnails', 'without_thumbnails')
    __title__ = 'found'

    def __init__(self, parent):
        super().__init__(parent)
        self.with_thumbnails = WithThumbnails(self)
        self.without_thumbnails = WithoutThumbnails(self)


class Unreadable(VideoSource):
    __slots__ = ('not_found', 'found')

    def __init__(self, database, source):
        super().__init__(database, source)
        self.not_found = NotFound(self)
        self.found = Found(self)


class Readable(VideoSource):
    __slots__ = ('not_found', 'found')

    def __init__(self, database, source):
        super().__init__(database, source)
        self.not_found = NotFound(self)
        self.found = ReadableFound(self)
