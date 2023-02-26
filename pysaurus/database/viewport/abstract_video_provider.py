import random
from abc import ABCMeta, abstractmethod
from typing import Sequence

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications
from pysaurus.video.video import Video


class AbstractVideoProvider(metaclass=ABCMeta):
    __slots__ = ("_database",)

    def __init__(self, database):
        self._database = database

    @abstractmethod
    def set_sources(self, paths):
        pass

    @abstractmethod
    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ):
        pass

    @abstractmethod
    def set_classifier_path(self, path):
        pass

    @abstractmethod
    def set_group(self, group_id):
        pass

    @abstractmethod
    def set_search(self, text, cond):
        pass

    @abstractmethod
    def set_sort(self, sorting):
        pass

    @abstractmethod
    def get_sources(self):
        pass

    @abstractmethod
    def get_grouping(self):
        pass

    @abstractmethod
    def convert_field_value_to_group_id(self, field_value):
        pass

    @abstractmethod
    def get_classifier_path(self):
        pass

    @abstractmethod
    def get_classifier_group_value(self, group_id):
        pass

    @abstractmethod
    def get_group(self):
        pass

    @abstractmethod
    def get_search(self):
        pass

    @abstractmethod
    def get_sort(self):
        pass

    @abstractmethod
    def reset_parameters(self, *layer_names: str):
        pass

    @abstractmethod
    def force_update(self, *layer_names: str):
        pass

    @abstractmethod
    def get_classifier_stats(self):
        pass

    @abstractmethod
    def get_all_videos(self):
        pass

    @abstractmethod
    def get_view(self):
        pass

    @abstractmethod
    def delete(self, video: Video):
        pass

    def get_unordered_state(self):
        """Get state excluding sorting state"""
        return {
            "sources": self.get_sources(),
            "grouping": self.get_grouping(),
            "path": self.get_classifier_path(),
            "group": self.get_group(),
            "search": self.get_search(),
        }

    def refresh(self):
        self.force_update("source")

    def get_group_def(self):
        group_def = self.get_grouping()
        return (
            group_def.to_dict(
                group_id=self.get_group(),
                groups=self.get_classifier_stats(),
            )
            if group_def
            else None
        )

    def get_search_def(self):
        search_def = self.get_search()
        return search_def.to_dict() if search_def else None

    def get_random_found_video(self) -> Video:
        videos = []
        for path in self.get_sources():
            videos.extend(self._database.get_videos(*path, found=True))
        if not videos:
            raise exceptions.NoVideos()
        return videos[random.randrange(len(videos))]

    def choose_random_video(self, open_video=True) -> str:
        video = self.get_random_found_video()
        self.reset_parameters("source", "grouping", "classifier", "group")
        self.set_search(str(video.video_id), "id")
        if open_video:
            video.filename.open()
        return video.filename.path

    def classifier_select_group(self, group_id: int):
        path = self.get_classifier_path()
        value = self.get_classifier_group_value(group_id)
        new_path = path + [value]
        self.set_classifier_path(new_path)
        self.set_group(0)

    def classifier_focus_prop_val(self, prop_name, field_value):
        self.set_groups(
            field=prop_name,
            is_property=True,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        self.get_view()
        group_id = self.convert_field_value_to_group_id(field_value)
        self.set_classifier_path([])
        self.get_view()
        # NB: here, classifier and grouping have same group array
        self.classifier_select_group(group_id)

    def classifier_back(self):
        path = self.get_classifier_path()
        self.set_classifier_path(path[:-1])
        self.set_group(0)

    def classifier_reverse(self) -> list:
        path = list(reversed(self.get_classifier_path()))
        self.set_classifier_path(path)
        return path

    def playlist(self) -> str:
        return str(self._database.to_xspf_playlist(self.get_view()).open())

    def select_from_view(self, selector: dict, return_videos=False):
        return functions.apply_selector(
            selector, self.get_view(), "video_id", return_videos
        )

    def apply_on_view(self, selector, db_fn_name, *db_fn_args):
        callable_methods = {
            "count_property_values": self._database.count_property_values,
            "edit_property_for_videos": self._database.edit_property_for_videos,
        }
        return callable_methods[db_fn_name](
            self.select_from_view(selector, return_videos=True), *db_fn_args
        )

    def register_notifications(self):
        self._database.notifier.set_manager(
            notifications.VideoDeleted, self.on_video_deleted
        )
        self._database.notifier.set_manager(
            notifications.FieldsModified, self.on_fields_modified
        )
        self._database.notifier.set_manager(
            notifications.PropertiesModified, self.on_properties_modified
        )

    def on_video_deleted(self, notification: notifications.VideoDeleted):
        self.delete(notification.video)

    def on_fields_modified(self, notification: notifications.FieldsModified):
        self._manage_attributes_modified(notification.fields, False)

    def on_properties_modified(self, notification: notifications.PropertiesModified):
        self._manage_attributes_modified(notification.fields, True)

    def _manage_attributes_modified(self, properties: Sequence[str], is_property=True):
        group_def = self.get_grouping()
        if (
            group_def
            and group_def.is_property is is_property
            and group_def.field in properties
        ):
            self.force_update("grouping")
            return True
