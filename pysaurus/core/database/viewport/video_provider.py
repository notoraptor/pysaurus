"""
Select sources
Select group
Search
Sort
"""
import random
from typing import Optional, Sequence

from pysaurus.core.database import notifications
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video
from pysaurus.core.database.viewport.layers.classifier_layer import ClassifierLayer
from pysaurus.core.database.viewport.layers.group_layer import GroupLayer
from pysaurus.core.database.viewport.layers.grouping_layer import GroupingLayer
from pysaurus.core.database.viewport.layers.search_layer import SearchLayer
from pysaurus.core.database.viewport.layers.sort_layer import SortLayer
from pysaurus.core.database.viewport.layers.source_layer import SourceLayer
from pysaurus.core.database.viewport.viewtools.video_array import VideoArray


class VideoProvider:
    __slots__ = (
        "database",
        "source_layer",
        "grouping_layer",
        "classifier_layer",
        "group_layer",
        "search_layer",
        "sort_layer",
        "view",
    )

    def __init__(self, database: Database):
        self.database = database
        self.view = []

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

        ##
        # if self.database.has_prop_type('category'):
        #     prop_category = self.database.get_prop_type('category')
        #     if prop_category.type is str and prop_category.multiple:
        #         self.grouping_layer.set_grouping(
        #             field=':category',
        #             sorting='field',
        #             reverse=False,
        #             allow_singletons=True,
        #             allow_multiple=True
        #         )
        ##

        self.source_layer.set_data(self.database)
        self.view = self.source_layer.run()
        assert isinstance(self.view, VideoArray)

    def set_source(self, paths: Sequence[Sequence[str]]):
        self.source_layer.set_sources(paths)
        self.view = self.source_layer.run()

    def set_groups(
        self,
        field: Optional[str],
        sorting: Optional[str] = None,
        reverse: Optional[bool] = None,
        allow_singletons: Optional[bool] = None,
        allow_multiple: Optional[bool] = None,
    ):
        self.grouping_layer.set_grouping(
            field=field,
            sorting=sorting,
            reverse=reverse,
            allow_singletons=allow_singletons,
            allow_multiple=allow_multiple,
        )
        self.group_layer.set_group_id(0)
        self.search_layer.reset_parameters()
        self.classifier_layer.reset_parameters()
        self.view = self.source_layer.run()

    def set_search(self, text: Optional[str], cond: Optional[str]):
        self.search_layer.set_search(text, cond)
        self.view = self.source_layer.run()

    def set_sort(self, sorting: Sequence[str]):
        self.sort_layer.set_sorting(sorting)
        self.view = self.source_layer.run()

    def set_group(self, group_id):
        self.group_layer.set_group_id(group_id)
        self.view = self.source_layer.run()

    def get_group_def(self):
        group_def = self.grouping_layer.get_grouping()
        if group_def:
            return {
                "field": group_def.field,
                "sorting": group_def.sorting,
                "reverse": group_def.reverse,
                "allowSingletons": group_def.allow_singletons,
                "allowMultiple": group_def.allow_multiple,
                "group_id": self.group_layer.get_group_id(),
                "nb_groups": self.classifier_layer.count_groups(),
                "groups": self.classifier_layer.get_stats(),
            }
        return None

    def get_search_def(self):
        search_def = self.search_layer.get_search()
        if search_def:
            return {"text": search_def.text, "cond": search_def.cond}
        return None

    def get_video(self, index: int) -> Video:
        return self.view[index]

    def load(self):
        self.source_layer.request_update()
        self.view = self.source_layer.run()

    def update_view(self):
        self.view = self.source_layer.run()

    def all_not_found(self):
        return all("not_found" in source for source in self.source_layer.get_sources())

    def get_random_found_video(self):
        # type: () -> Video
        videos = []
        for path in self.source_layer.get_sources():
            videos.extend(self.database.get_videos(*path, found=True))
        if not videos:
            raise RuntimeError("No videos available.")
        return videos[random.randrange(len(videos))]

    def get_all_videos(self):
        return self.source_layer.videos()

    def get_view(self):
        return list(self.view)

    def on_video_deleted(self, notification: notifications.VideoDeleted):
        self.source_layer.delete_video(notification.video)
        self.view = self.source_layer.run()

    def on_fields_modified(self, notification: notifications.FieldsModified):
        self.on_properties_modified(notification.fields)

    def on_properties_modified(self, properties: Sequence[str]):
        self.source_layer.update_index()
        gdef = self.grouping_layer.get_grouping()
        if gdef:
            field = gdef.field[1:] if gdef.field[0] == ":" else gdef.field
            if field in properties:
                self.grouping_layer.request_update()
                self.view = self.source_layer.run()
                return True

    def register_notifications(self):
        self.database.notifier.set_manager(
            notifications.VideoDeleted, self.on_video_deleted
        )
        self.database.notifier.set_manager(
            notifications.FieldsModified, self.on_fields_modified
        )
