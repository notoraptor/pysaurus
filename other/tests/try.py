from typing import List, Tuple

from pysaurus.application.application import Application
from pysaurus.core import functions
from pysaurus.core.job_notifications import (
    global_notify_job_progress,
    global_notify_job_start,
)
from pysaurus.core.profiling import Profiler
from pysaurus.video import Video
from pysaurus.video.video_features import VideoFeatures


class Val:
    __slots__ = "v", "a"
    __attrs__ = functions.class_get_public_attributes(
        Video,
        exclude=[
            "audio_languages",
            "duration",
            "duration_time_base",
            "errors",
            "frame_rate_den",
            "frame_rate_num",
            "meta_title",
            "meta_title_numeric",
            "moves",
            "properties",
            "quality_compression",
            "raw_microseconds",
            "raw_properties",
            "raw_seconds",
            "subtitle_languages",
            "thumbnail_path",
            "video_id",
        ],
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
    def __init__(self, string_properties: Tuple[List[str], List[str]]):
        self.p = string_properties

    def get_things(self, video: Video) -> List[PropVal]:
        ps = video.raw_properties
        return [PropVal(n, ps[n]) for n in self.p[0] if n in ps] + [
            PropVal(n, v) for n in self.p[1] if n in ps for v in ps[n]
        ]


def _profile_video_to_json(database):
    batch = 100
    with Profiler("to_json"):
        for _ in range(batch):
            list(VideoFeatures.to_json(v) for v in database.query()[:100])
    with Profiler("json"):
        for _ in range(batch):
            list(VideoFeatures.json(v) for v in database.query()[:100])


def _check_prop_val(database, pgf):
    for video in database.query():
        if video.raw_properties:
            print(video.filename)
            for pv in pgf.get_things(video):
                print("\t", pv)
            break


def main():
    application = Application()
    database = application.open_database_from_name("adult videos")
    # videos = list(database.select_videos_fields(
    #     ["filename", "thumbnail_path", "video_id"], "readable", "with_thumbnails"
    # ))
    # print(len(videos))
    all_attributes = functions.class_get_public_attributes(Video, wrapper=sorted)
    print("Video attributes:", len(Val.__attrs__))
    for attribute in Val.__attrs__:
        print("\t", attribute)
    print("Video all attributes:", all_attributes)
    for attribute in all_attributes:
        print("\t", attribute)

    pgf = PropGetterFactory(database.get_string_properties())

    # _profile_video_to_json(database)
    # _check_prop_val(database, pgf)

    input("Hello?")
    thing_to_filenames = {}
    with Profiler("collect video things"):
        with Profiler("Collect filename to tags"):
            filename_to_things = {
                video.filename: [Val(video, i) for i in range(len(Val.__attrs__))]
                + pgf.get_things(video)
                + video.terms()
                for video in database.query()
            }
        nb_videos = len(filename_to_things)
        with Profiler("Collect tag to filenames"):
            global_notify_job_start("collect_tags", nb_videos, "videos")
            for i, (filename, things) in enumerate(filename_to_things.items()):
                for thing in things:
                    try:
                        thing_to_filenames.setdefault(thing, []).append(filename)
                    except Exception as exc:
                        raise Exception(thing) from exc
                if (i + 1) % 500 == 0:
                    global_notify_job_progress("collect_tags", None, i + 1, nb_videos)
            global_notify_job_progress("collect_tags", None, nb_videos, nb_videos)

    print("Finished collecting")
    print("Videos:", len(filename_to_things))
    print("Total unique tags:", len(thing_to_filenames))
    print("Total tags:", sum(len(tags) for tags in filename_to_things.values()))
    print(
        "Example japanese",
        len(thing_to_filenames.get(PropVal("category", "japanese"), ())),
    )
    input("Hello!")


if __name__ == "__main__":
    main()
