from pysaurus.application.application import Application
from pysaurus.core import functions
from pysaurus.core.profiling import Profiler
from pysaurus.video import Video


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

    val = property(lambda self: getattr(self.v, self.__attrs__[self.a]))

    def __hash__(self):
        return hash((type(self), self.a, self.val))

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self.a == other.a
            and self.val == other.val
        )


def main():
    application = Application()
    database = application.open_database_from_name("adult videos")
    # videos = list(database.select_videos_fields(
    #     ["filename", "thumbnail_path", "video_id"], "readable", "with_thumbnails"
    # ))
    # print(len(videos))
    print("Video attributes:", len(Val.__attrs__))
    for attribute in Val.__attrs__:
        print("\t", attribute)

    filename_to_tags = {}
    tag_to_filenames = {}
    input("Hello?")
    with Profiler("collect video things"):
        for i, video in enumerate(database.query()):
            things = [Val(video, i) for i in range(len(Val.__attrs__))] + video.terms()
            filename_to_tags[video.filename] = things
            for thing in things:
                try:
                    tag_to_filenames.setdefault(thing, []).append(video.filename)
                except Exception as exc:
                    raise Exception(thing) from exc
            if (i + 1) % 500 == 0:
                print("Collecting video", i + 1)

    indexer = {
        "filename_to_tags": filename_to_tags,
        "tag_to_filenames": tag_to_filenames,
    }
    print("Finished collecting")
    print("Videos:", len(filename_to_tags))
    print("Total unique tags:", len(tag_to_filenames))
    print("Total tags:", sum(len(tags) for tags in filename_to_tags.values()))
    input("Hello!")


if __name__ == "__main__":
    main()
