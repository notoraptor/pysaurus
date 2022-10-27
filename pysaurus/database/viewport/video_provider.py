"""
Select sources
Select group
Search
Sort
"""
import random
from typing import Optional, Sequence

from pysaurus.application import exceptions
from pysaurus.core import notifications
from pysaurus.database.database import Database
from pysaurus.database.video import Video
from pysaurus.database.viewport.layers.classifier_layer import ClassifierLayer
from pysaurus.database.viewport.layers.group_layer import GroupLayer
from pysaurus.database.viewport.layers.grouping_layer import GroupingLayer
from pysaurus.database.viewport.layers.search_layer import SearchLayer
from pysaurus.database.viewport.layers.sort_layer import SortLayer
from pysaurus.database.viewport.layers.source_layer import SourceLayer
from pysaurus.database.viewport.viewtools.group_def import GroupDef
from pysaurus.database.viewport.viewtools.video_array import VideoArray


class VideoProvider:
    __slots__ = (
        "database",
        "source_layer",
        "grouping_layer",
        "classifier_layer",
        "group_layer",
        "search_layer",
        "sort_layer",
    )

    def __init__(self, database: Database):
        self.database = database

        self.source_layer = SourceLayer(database)
        self.grouping_layer = GroupingLayer(database)
        self.classifier_layer = ClassifierLayer(database)
        self.group_layer = GroupLayer(database)
        self.search_layer = SearchLayer(database)
        self.sort_layer = SortLayer(database)

        self.source_layer.set_sub_layer(self.grouping_layer)
        self.grouping_layer.set_sub_layer(self.classifier_layer)
        self.classifier_layer.set_sub_layer(self.group_layer)
        self.group_layer.set_sub_layer(self.search_layer)
        self.search_layer.set_sub_layer(self.sort_layer)

        self.source_layer.set_data(self.database)

    def set_source(self, paths: Sequence[Sequence[str]]):
        self.source_layer.set_sources(paths)

    def set_groups(self, **group_def_args):
        self.grouping_layer.set_grouping(**GroupDef.get_args_from(group_def_args))
        self.classifier_layer.reset_parameters()
        self.group_layer.set_group_id(0)
        self.search_layer.reset_parameters()

    def set_group(self, group_id):
        self.group_layer.set_group_id(group_id)

    def set_search(self, text: Optional[str], cond: Optional[str]):
        self.search_layer.set_search(text, cond)

    def set_sort(self, sorting: Sequence[str]):
        self.sort_layer.set_sorting(sorting)

    def refresh(self):
        self.source_layer.request_update()

    def get_group_def(self):
        group_def = self.grouping_layer.get_grouping()
        return (
            group_def.to_dict(
                group_id=self.group_layer.get_group_id(),
                groups=self.classifier_layer.get_stats(),
            )
            if group_def
            else None
        )

    def get_search_def(self):
        search_def = self.search_layer.get_search()
        return search_def.to_dict() if search_def else None

    def get_random_found_video(self) -> Video:
        videos = []
        for path in self.source_layer.get_sources():
            videos.extend(self.database.get_videos(*path, found=True))
        if not videos:
            raise exceptions.NoVideos()
        return videos[random.randrange(len(videos))]

    def get_all_videos(self):
        return self.source_layer.videos()

    def get_view(self) -> VideoArray:
        return self.source_layer.run()

    def register_notifications(self):
        self.database.notifier.set_manager(
            notifications.VideoDeleted, self.on_video_deleted
        )
        self.database.notifier.set_manager(
            notifications.FieldsModified, self.on_fields_modified
        )
        self.database.notifier.set_manager(
            notifications.PropertiesModified, self.on_properties_modified
        )

    def on_video_deleted(self, notification: notifications.VideoDeleted):
        self.source_layer.delete_video(notification.video)

    def on_fields_modified(self, notification: notifications.FieldsModified):
        self._manage_attributes_modified(notification.fields, False)

    def on_properties_modified(self, notification: notifications.PropertiesModified):
        self._manage_attributes_modified(notification.fields, True)

    def _manage_attributes_modified(self, properties: Sequence[str], is_property=True):
        group_def = self.grouping_layer.get_grouping()
        if (
            group_def
            and group_def.is_property is is_property
            and group_def.field in properties
        ):
            self.grouping_layer.request_update()
            return True
