from typing import List

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import System
from pysaurus.core.profiling import Profiler
from pysaurus.database import path_utils
from pysaurus.database.database import Database
from pysaurus.database.miniature_tools.miniature import Miniature


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
        paths = path_utils.load_path_list_file(list_file_path)
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
            raise exceptions.UnknownVideoFilename(filename)
        return None

    def get_unreadable_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[VideoState]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__unreadable:
            return self.__unreadable[filename]
        if required:
            raise exceptions.UnknownVideoFilename(filename)
        return None

    def get_unreadable_from_id(self, video_id, required=True):
        # type: (int, bool) -> Optional[VideoState]
        if (
            video_id in self.__id_to_video
            and self.__id_to_video[video_id].filename in self.__unreadable
        ):
            return self.__id_to_video[video_id]
        if required:
            raise exceptions.UnknownVideoID(video_id)
        return None

    def remove_videos_not_found(self):
        nb_removed = 0
        for video in list(self.__videos.values()):
            if not video.filename.isfile():
                self.delete_video(video, save=False)
                nb_removed += 1
        if nb_removed:
            self.__notifier.notify(notifications.VideosNotFoundRemoved(nb_removed))
            self.save()

    def reset(self, reset_thumbnails=False, reset_miniatures=False):
        self.__videos.clear()
        self.__unreadable.clear()
        self.__discarded.clear()
        self.__json_path.delete()
        if reset_miniatures:
            self.__miniatures_path.delete()
        if reset_thumbnails:
            self.__thumb_folder.delete()

    def list_files(self, output_name):
        with open(output_name, "wb") as file:
            file.write("# Videos\n".encode())
            for file_name in sorted(self.__videos):
                file.write(("%s\n" % str(file_name)).encode())
            file.write("# Unreadable\n".encode())
            for file_name in sorted(self.__unreadable):
                file.write(("%s\n" % str(file_name)).encode())
            file.write("# Discarded\n".encode())
            for file_name in sorted(self.__discarded):
                file.write(("%s\n" % str(file_name)).encode())

    def save_miniatures(self, miniatures: List[Miniature]):
        with open(self.__miniatures_path.path, "w") as output_file:
            json.dump([m.to_dict() for m in miniatures], output_file)
