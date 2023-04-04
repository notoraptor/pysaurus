from pysaurus.application.application import Application
from pysaurus.core import functions
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

    def __hash__(self):
        return hash((type(self), self.a, self.k))

    def __eq__(self, other):
        return type(self) is type(other) and self.a == other.a and self.k == other.k


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

    batch = 100
    with Profiler("to_json"):
        for _ in range(batch):
            list(VideoFeatures.to_json(v) for v in database.query()[:100])
    with Profiler("json"):
        for _ in range(batch):
            list(VideoFeatures.json(v) for v in database.query()[:100])

    input("Hello?")
    thing_to_filenames = {}
    with Profiler("collect video things"):
        with Profiler("Collect filename to tags"):
            filename_to_things = {
                video.filename: [Val(video, i) for i in range(len(Val.__attrs__))]
                + video.terms()
                for video in database.query()
            }
        with Profiler("Collect tag to filenames"):
            for i, (filename, things) in enumerate(filename_to_things.items()):
                for thing in things:
                    try:
                        thing_to_filenames.setdefault(thing, []).append(filename)
                    except Exception as exc:
                        raise Exception(thing) from exc
                if (i + 1) % 500 == 0:
                    print("Collecting video", i + 1)

    indexer = {
        "filename_to_things": filename_to_things,
        "thing_to_filenames": thing_to_filenames,
    }
    print("Finished collecting")
    print("Videos:", len(filename_to_things))
    print("Total unique tags:", len(thing_to_filenames))
    print("Total tags:", sum(len(tags) for tags in filename_to_things.values()))
    input("Hello!")


if __name__ == "__main__":
    main()
