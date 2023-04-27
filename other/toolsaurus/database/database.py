from typing import Iterable, List, Optional, Union

import ujson as json

from other.toolsaurus.database.db_cache import DbCache
from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.modules import System
from pysaurus.core.profiling import Profiler
from pysaurus.database.database import Database
from pysaurus.miniature.miniature import Miniature
from pysaurus.video import Video


class ExtendedDatabase(Database):
    __slots__ = ("sys_is_case_insensitive", "__db_cache")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__db_cache = DbCache(self)
        self.sys_is_case_insensitive = System.is_case_insensitive(
            self.__paths.db_folder.path
        )

    def get_valid_videos(self):
        return self.get_videos("readable", "found", "with_thumbnails")

    @classmethod
    @Profiler.profile_method()
    def load_from_list_file_path(
        cls,
        list_file_path,
        notifier=None,
        update=True,
        ensure_miniatures=True,
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
        if update:
            database.refresh(ensure_miniatures)
        return database

    def get_unreadable_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[Video]
        video_id = self.get_video_id(filename)
        unreadable = self.read_video_field(video_id, "unreadable")
        assert unreadable
        return self.describe_videos([video_id])[0]

    def remove_videos_not_found(self):
        nb_removed = 0
        with self.to_save() as saver:
            for video in self.get_videos():
                if not video.filename.isfile():
                    self.delete_video(video.video_id)
                    nb_removed += 1
            if nb_removed:
                self.notifier.notify(notifications.VideosNotFoundRemoved(nb_removed))
                saver.to_save = nb_removed

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
        with open(self.__paths.miniatures_path.path, "w") as output_file:
            json.dump([m.to_dict() for m in miniatures], output_file)

    def get_video_string(self, video_id: int) -> str:
        return self.describe_videos([video_id])[0]

    def get_videos(self, *flags, **forced_flags):
        return self.__db_cache(*flags, **forced_flags)


def load_list_file(list_file_path: Union[AbsolutePath, str]) -> Iterable[str]:
    strings = []
    list_file_path = AbsolutePath.ensure(list_file_path)
    if list_file_path.isfile():
        with open(list_file_path.path, "r") as list_file:
            for line in list_file:
                line = line.strip()
                if line and line[0] != "#":
                    strings.append(line)
    return strings


def load_path_list_file(list_file_path: AbsolutePath) -> Iterable[AbsolutePath]:
    return [AbsolutePath(string) for string in load_list_file(list_file_path)]
