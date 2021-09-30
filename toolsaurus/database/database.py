from typing import List
from typing import Optional

import ujson as json

import toolsaurus.application.exceptions
from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.modules import System
from pysaurus.core.profiling import Profiler
from pysaurus.database.database import Database
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.video import Video
from pysaurus.database.video_state import VideoState


class ExtendedDatabase(Database):
    __slots__ = ("sys_is_case_insensitive",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sys_is_case_insensitive = System.is_case_insensitive(self.folder.path)

    def get_valid_videos(self):
        return self.get_videos("readable", "found", "with_thumbnails")

    @classmethod
    @Profiler.profile()
    def load_from_list_file_path(
        cls,
        list_file_path,
        notifier=None,
        update=True,
        ensure_miniatures=True,
        reset=False,
        clear_old_folders=False,
    ):
        paths = load_path_list_file(list_file_path)
        database_folder = list_file_path.get_directory()
        database = cls(
            path=database_folder,
            folders=paths,
            notifier=notifier,
            clear_old_folders=clear_old_folders,
        )
        if reset:
            database.reset()
        if update:
            database.refresh(ensure_miniatures)
        return database

    def get_video_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[Video]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__videos:
            return self.__videos[filename]
        if required:
            raise toolsaurus.application.exceptions.UnknownVideoFilename(filename)
        return None

    def get_unreadable_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[VideoState]
        video = self.get_video_from_filename(filename, required)
        assert video.unreadable
        return video

    def get_unreadable_from_id(self, video_id, required=True):
        # type: (int, bool) -> Optional[VideoState]
        if video_id in self.__id_to_video:
            video = self.__id_to_video[video_id]
            assert video.unreadable
            return video
        if required:
            raise toolsaurus.application.exceptions.UnknownVideoID(video_id)
        return None

    def remove_videos_not_found(self):
        nb_removed = 0
        for video in self.get_videos():
            if not video.filename.isfile():
                self.delete_video(video.video_id, save=False)
                nb_removed += 1
        if nb_removed:
            self.__notifier.notify(notifications.VideosNotFoundRemoved(nb_removed))
            self.save()

    def reset(self, reset_thumbnails=False, reset_miniatures=False):
        self.__videos.clear()
        self.__json_path.delete()
        if reset_miniatures:
            self.__miniatures_path.delete()
        if reset_thumbnails:
            self.__thumb_folder.delete()

    def list_files(self, output_name):
        readable_videos = self.get_videos("readable")
        unreadable_videos = self.get_videos("unreadable")
        discarded_videos = self.get_videos("discarded")
        with open(output_name, "wb") as file:
            file.write("# Videos\n".encode())
            for file_name in sorted(readable_videos):
                file.write(("%s\n" % str(file_name)).encode())
            file.write("# Unreadable\n".encode())
            for file_name in sorted(unreadable_videos):
                file.write(("%s\n" % str(file_name)).encode())
            file.write("# Discarded\n".encode())
            for file_name in sorted(discarded_videos):
                file.write(("%s\n" % str(file_name)).encode())

    def save_miniatures(self, miniatures: List[Miniature]):
        with open(self.__miniatures_path.path, "w") as output_file:
            json.dump([m.to_dict() for m in miniatures], output_file)

    def get_video_id(self, filename):
        return self.__videos[AbsolutePath.ensure(filename)].video_id


def load_list_file(list_file_path):
    # type: (Union[AbsolutePath, str]) -> Iterable[str]
    strings = []
    list_file_path = AbsolutePath.ensure(list_file_path)
    if list_file_path.isfile():
        with open(list_file_path.path, "r") as list_file:
            for line in list_file:
                line = line.strip()
                if line and line[0] != "#":
                    strings.append(line)
    return strings


def load_path_list_file(list_file_path):
    # type: (AbsolutePath) -> Iterable[AbsolutePath]
    return [AbsolutePath(string) for string in load_list_file(list_file_path)]
