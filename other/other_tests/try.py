import logging
from typing import List

from pysaurus.core import functions
from pysaurus.core.informer import Informer
from pysaurus.core.profiling import Profiler
from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo as Video
from tests.utils_testing import get_database

SAME_ORDER_FIELD = {
    "length": "raw_seconds",
    "not_found": "!found",
    "raw_microseconds": "raw_seconds",
    "readable": "!unreadable",
    "size": "file_size",
    "without_thumbnails": "!with_thumbnails",
}


class Val:
    __slots__ = "v", "a"
    __attrs__ = functions.class_get_public_attributes(
        Video,
        exclude=[
            "audio_languages",
            "duration",
            "duration_time_base",
            "errors",
            "filename_length",
            "frame_rate_den",
            "frame_rate_num",
            "properties",
            "meta_title",
            "meta_title_numeric",
            "moves",
            "properties",
            "quality_compression",
            "raw_microseconds",
            "subtitle_languages",
            "video_id",
        ]
        + list(SAME_ORDER_FIELD),
        wrapper=sorted,
    )

    def __init__(self, video: Video, attr_id: int):
        self.v = video
        self.a = attr_id

    k = property(lambda self: getattr(self.v, self.__attrs__[self.a]))

    def __str__(self):
        return f"{type(self).__name__}({self.__attrs__[self.a]}, {self.k})"

    __repr__ = __str__

    def __hash__(self):
        return hash((type(self), self.a, self.k))

    def __eq__(self, other):
        return type(self) is type(other) and self.a == other.a and self.k == other.k


class PropVal:
    def __init__(self, n, v):
        self.k = (n, v)

    def __str__(self):
        return f"{type(self).__name__}{self.k}"

    __repr__ = __str__

    def __hash__(self):
        return hash((type(self), self.k))

    def __eq__(self, other):
        return type(self) is type(other) and self.k == other.k


class PropGetterFactory:
    def __init__(self, string_properties: List[str]):
        self.p = string_properties
        self.z = list(enumerate(self.p))
        self.n_to_i = {n: i for i, n in self.z}

    def get_things(self, video: Video) -> List[PropVal]:
        ps = video.properties
        return [PropVal(i, v) for i, n in self.z if n in ps for v in ps[n]]

    def thing(self, n, v):
        return PropVal(self.n_to_i[n], v)


def _display_all_video_attributes():
    all_attributes = functions.class_get_public_attributes(Video, wrapper=sorted)
    print("Video all attributes:", len(all_attributes))
    for attribute in all_attributes:
        print("\t", attribute)


def _get_string_properties(database):
    return [pt["name"] for pt in database.get_prop_types() if pt["type"] == "str"]


def main():
    notifier = Informer.default()
    database = get_database()
    print("Video attributes:", len(Val.__attrs__))
    for attribute in Val.__attrs__:
        print("\t", attribute)

    pgf = PropGetterFactory(_get_string_properties(database))

    input("Hello?")
    thing_to_filenames = {}
    with Profiler("collect video things"):
        with Profiler("Collect filename to tags"):
            filename_to_things = {
                video.filename: [Val(video, i) for i in range(len(Val.__attrs__))]
                + pgf.get_things(video)
                + video.terms()
                for video in database._jsondb_get_cached_videos()
            }
        nb_videos = len(filename_to_things)
        with Profiler("Collect tag to filenames"):
            notifier.task("collect_tags", nb_videos, "videos")
            for i, (filename, things) in enumerate(filename_to_things.items()):
                for thing in things:
                    try:
                        thing_to_filenames.setdefault(thing, []).append(filename)
                    except Exception as exc:
                        raise Exception(thing) from exc
                if (i + 1) % 500 == 0:
                    notifier.progress("collect_tags", i + 1, nb_videos)
            notifier.progress("collect_tags", nb_videos, nb_videos)

    print("Finished collecting")
    print("Videos:", len(filename_to_things))
    print("Total unique tags:", len(thing_to_filenames))
    print("Total tags:", sum(len(tags) for tags in filename_to_things.values()))
    print(
        "Example japanese",
        len(thing_to_filenames.get(pgf.thing("certified category", "japanese"), ())),
    )
    input("Hello!")


def main2():
    logging.basicConfig(level=logging.NOTSET)
    db = get_database()
    videos = db._jsondb_get_cached_videos(**{"readable": True})
    videos.sort(key=lambda v: v.bit_rate)
    vs = [
        v
        for v in videos
        if v.filename.path
        == r"N:\donnees\autres\p\Yuahentai - her recipe is for a creampie.mp4"
    ]
    (v,) = vs
    for video in (videos[0], videos[-1], v):
        print(video.filename)
        print("\tframe_rate", video.frame_rate)
        print("\twidth", video.width)
        print("\theight", video.height)
        print("\tbit_depth", video.bit_depth)
        print("\taudio_codec", video.audio_codec)
        print("\tsample_rate", video.sample_rate)
        print("\taudio_bits", video.audio_bits)
        print("\traw_seconds", video.raw_seconds, video.length)
        print("\tfile_size", video.size)
        print("\texpected_raw_size", video.expected_raw_size)
        print("\tbit_rate", video.bit_rate, "/ s")


def main3():
    path = r"N:\donnees\autres\p\Yuahentai - her recipe is for a creampie.mp4"
    import pprint
    from pysaurus.video_raptor.video_raptor_pyav import PythonVideoRaptor

    vr = PythonVideoRaptor()
    info = vr._get_info(path)
    pprint.pprint(info)


if __name__ == "__main__":
    main2()
