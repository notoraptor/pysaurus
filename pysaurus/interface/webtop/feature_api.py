import sys
from typing import Optional

from pysaurus.core import notifications
from pysaurus.core.components import FileSize, Duration
from pysaurus.core.database.database import Database
from pysaurus.core.database.properties import PropType
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_features import VideoFeatures
from pysaurus.core.database.viewport.layers.source_layer import SourceLayer
from pysaurus.core.database.viewport.video_provider import VideoProvider
from pysaurus.core.functions import compute_nb_pages
from pysaurus.interface.webtop import iutils
from pysaurus.application import Application


class FeatureAPI:
    def __init__(self, notifier=None):
        self.notifier = notifier
        self.application = Application(self.notifier)
        self.database = None  # type: Optional[Database]
        self.provider = None  # type: Optional[VideoProvider]

    # Utilities.

    def _selector_to_indices(self, selector: dict):
        if selector["all"]:
            exclude = set(selector["exclude"])
            video_indices = [
                video.video_id
                for video in self.provider.get_view()
                if video.video_id not in exclude
            ]
        else:
            video_indices = set(selector["include"])
        return video_indices

    def _selector_to_videos(self, selector: dict):
        if selector["all"]:
            exclude = set(selector["exclude"])
            videos = [
                video
                for video in self.provider.get_view()
                if video.video_id not in exclude
            ]
        else:
            include = set(selector["include"])
            videos = [
                video for video in self.provider.get_view() if video.video_id in include
            ]
        return videos

    # Tk dialog boxes.

    def select_directory(self):
        return iutils.select_directory()

    def select_files(self):
        return iutils.select_many_files_to_open()

    def select_file(self):
        return iutils.select_file_to_open()

    # Constant getters.

    def get_constants(self):
        return {
            "PYTHON_DEFAULT_SOURCES": SourceLayer.DEFAULT_SOURCE_DEF,
            "PYTHON_APP_NAME": self.application.app_name,
        }

    def list_databases(self):
        return [{"name": path.title, "path": str(path)} for path in self.application.get_database_paths()]

    # Provider getters.

    def backend(self, callargs, page_size, page_number, selector=None):
        if callargs:
            ret = getattr(self, callargs[0])(*callargs[1:])
            if ret is not None:
                print("Ignored value returned by", callargs, file=sys.stderr)
                print(ret, file=sys.stderr)
        return self.get_info_and_videos(page_size, page_number, selector)

    def get_info_and_videos(self, page_size, page_number, selector=None):
        # Backend state.
        real_nb_videos = len(self.provider.get_view())
        if selector:
            view = self._selector_to_videos(selector)
        else:
            view = self.provider.get_view()
        nb_videos = len(view)
        nb_pages = compute_nb_pages(nb_videos, page_size)
        videos = []
        if nb_videos:
            page_number = min(max(0, page_number), nb_pages - 1)
            start = page_size * page_number
            end = min(start + page_size, nb_videos)
            videos = [VideoFeatures.to_json(view[index]) for index in range(start, end)]
        sources = self.provider.source_layer.get_sources()
        prop_types = self.get_prop_types()
        return {
            "pageSize": page_size,
            "pageNumber": page_number,
            "nbVideos": nb_videos,
            "realNbVideos": real_nb_videos,
            "nbPages": nb_pages,
            "validSize": str(FileSize(sum(video.file_size for video in view))),
            "validLength": str(
                Duration(
                    sum(
                        video.raw_microseconds
                        for video in view
                        if isinstance(video, Video)
                    )
                )
            ),
            "notFound": all("not_found" in source for source in sources),
            "sources": sources,
            "groupDef": self.provider.get_group_def(),
            "searchDef": self.provider.get_search_def(),
            "sorting": self.provider.sort_layer.get_sorting(),
            "videos": videos,
            "path": self.provider.classifier_layer.get_path(),
            "properties": prop_types,
            "definitions": {prop["name"]: prop for prop in prop_types},
        }

    # Provider setters.

    def set_sources(self, paths):
        self.provider.set_source(paths)

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ):
        self.provider.set_groups(
            field=field,
            is_property=is_property,
            sorting=sorting,
            reverse=reverse,
            allow_singletons=allow_singletons,
        )

    def set_group(self, group_id):
        self.provider.set_group(group_id)

    def set_search(self, search_text: str, search_type: str):
        self.provider.set_search(search_text, search_type)

    def set_sorting(self, sorting):
        self.provider.set_sort(sorting)

    def classifier_select_group(self, group_id):
        prop_name = self.provider.grouping_layer.get_grouping().field
        path = self.provider.classifier_layer.get_path()
        value = self.provider.classifier_layer.get_group_value(group_id)
        new_path = path + [value]
        self.provider.classifier_layer.set_path(new_path)
        self.provider.group_layer.set_group_id(0)
        self.database.notifier.notify(notifications.PropertiesModified([prop_name]))

    def classifier_focus_prop_val(self, prop_name, field_value):
        self.set_groups(prop_name, True, "count", True, True)
        self.provider.get_view()
        group_id = self.provider.grouping_layer.get_group_id(field_value)
        self.provider.classifier_layer.set_path([])
        self.provider.classifier_layer.run()
        self.classifier_select_group(group_id)

    def classifier_back(self):
        prop_name = self.provider.grouping_layer.get_grouping().field
        path = self.provider.classifier_layer.get_path()
        self.provider.classifier_layer.set_path(path[:-1])
        self.provider.group_layer.set_group_id(0)
        self.database.notifier.notify(notifications.PropertiesModified([prop_name]))

    def classifier_reverse(self):
        path = list(reversed(self.provider.classifier_layer.get_path()))
        self.provider.classifier_layer.set_path(path)
        return path

    # Database actions without modifications.

    def open_random_video(self):
        return str(self.provider.get_random_found_video().filename.open())

    def open_video(self, video_id):
        self.database.get_from_id(video_id).filename.open()

    def open_containing_folder(self, video_id):
        return str(self.database.get_from_id(video_id).filename.locate_file())

    # Database getters.

    def get_prop_types(self):
        props = sorted(self.database.get_prop_types(), key=lambda prop: prop.name)
        return [prop.to_json() for prop in props]

    def count_prop_values(self, name, selector):
        value_to_count = self.database.count_property_values(
            name, self._selector_to_indices(selector)
        )
        return sorted(value_to_count.items())

    # Database setters.

    def add_prop_type(self, prop_name, prop_type, prop_default, prop_multiple):
        if prop_type == "float":
            if isinstance(prop_default, list):
                prop_default = [float(element) for element in prop_default]
            else:
                prop_default = float(prop_default)
        self.database.add_prop_type(PropType(prop_name, prop_default, prop_multiple))
        return self.get_prop_types()

    def delete_prop_type(self, name):
        self.database.remove_prop_type(name)
        return self.get_prop_types()

    def rename_property(self, old_name, new_name):
        self.database.rename_prop_type(old_name, new_name)
        return self.get_prop_types()

    def convert_prop_to_unique(self, name):
        self.database.convert_prop_to_unique(name)
        return self.get_prop_types()

    def convert_prop_to_multiple(self, name):
        self.database.convert_prop_to_multiple(name)
        return self.get_prop_types()

    # Database setters + provider updated.

    def delete_video(self, video_id):
        self.database.delete_video(self.database.get_from_id(video_id))

    def rename_video(self, video_id, new_title):
        self.database.change_video_file_title(
            self.database.get_from_id(video_id), new_title
        )
        self.provider.refresh()

    def edit_property_for_videos(self, name, selector, to_add, to_remove):
        self.database.edit_property_for_videos(
            name, self._selector_to_indices(selector), to_add, to_remove
        )

    def set_video_properties(self, video_id, properties):
        self.database.set_video_properties(
            self.database.get_video_from_id(video_id), properties
        )

    def fill_property_with_terms(self, prop_name, only_empty=False):
        self.database.fill_property_with_terms(
            self.provider.get_all_videos(), prop_name, only_empty
        )

    def delete_property_value(self, name, values):
        return self.database.delete_property_value(
            self.provider.get_all_videos(), name, values
        )

    def edit_property_value(self, name, old_values, new_value):
        self.database.edit_property_value(
            self.provider.get_all_videos(), name, old_values, new_value
        )

    def move_property_value(self, old_name, values, new_name):
        self.database.move_property_value(
            self.provider.get_all_videos(), old_name, values, new_name
        )

    def classifier_concatenate_path(self, to_property):
        path = self.provider.classifier_layer.get_path()
        from_property = self.provider.grouping_layer.get_grouping().field
        self.provider.classifier_layer.set_path([])
        self.provider.group_layer.set_group_id(0)
        self.database.move_concatenated_prop_val(
            self.provider.get_all_videos(), path, from_property, to_property
        )
