from typing import Optional

from pysaurus.core.components import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.database.properties import PropType
from pysaurus.core.database.video_features import VideoFeatures
from pysaurus.core.database.video_filtering import get_usable_source_tree
from pysaurus.core.database.video_provider import VideoProvider
from pysaurus.core.functions import compute_nb_pages, to_json_value


class FeatureAPI:
    def __init__(self):
        self.database = None  # type: Optional[Database]
        self.provider = None  # type: Optional[VideoProvider]

    # View features.

    def set_sources(self, paths):
        self.provider.set_source(paths)

    def set_groups(
        self,
        field,
        sorting=None,
        reverse=None,
        allow_singletons=None,
        allow_multiple=None,
    ):
        self.provider.set_groups(
            field, sorting, reverse, allow_singletons, allow_multiple
        )

    def set_group(self, index):
        self.provider.set_group(index)

    def set_search(self, search_text: str, search_type: str):
        self.provider.set_search(search_text, search_type)

    def set_sorting(self, sorting):
        self.provider.set_sort(sorting)

    def get_info_and_videos(self, page_size, page_number, video_indices=()):
        view = self.provider.get_view()
        if video_indices:
            video_indices = set(video_indices)
            view = [video for video in view if video.video_id in video_indices]
        videos = []
        nb_videos = len(view)
        nb_pages = compute_nb_pages(nb_videos, page_size)
        if nb_videos:
            if page_number < 0:
                page_number = 0
            if page_number >= nb_pages:
                page_number = nb_pages - 1
            start = page_size * page_number
            end = min(start + page_size, nb_videos)
            videos = [
                VideoFeatures.to_json(view[index], local_id=index)
                for index in range(start, end)
            ]
        return {
            "nbVideos": nb_videos,
            "realNbVideos": self.provider.count(),
            "nbPages": nb_pages,
            "validSize": str(self.provider.get_view_file_size(view)),
            "validLength": str(self.provider.get_view_duration(view)),
            "nbGroups": self.provider.count_groups(),
            "notFound": self.provider.all_not_found(),
            "sources": self.provider.get_sources(),
            "groupDef": self.provider.get_group_def(),
            "searchDef": self.provider.get_search_def(),
            "sorting": self.provider.get_sorting(),
            "sourceTree": get_usable_source_tree(),
            "videos": videos,
            "pageNumber": page_number,
            "properties": self.get_prop_types(),
            "path": self.provider.classifier_layer.get_path(),
        }

    def get_view_indices(self):
        return self.provider.get_view_indices()

    def open_video(self, index):
        try:
            return str(self.provider.get_video(index).filename.open())
        except OSError:
            return False

    def open_video_from_filename(self, filename):
        try:
            return str(AbsolutePath.ensure(filename).open())
        except OSError:
            return False

    def open_containing_folder(self, index):
        video = self.provider.get_video(index)
        ret = video.filename.open_containing_folder()
        return str(ret) if ret else None

    def open_random_video(self):
        assert not self.provider.all_not_found()
        return str(self.provider.get_random_found_video().filename.open())

    def delete_video(self, index):
        return self.provider.delete_video(index)

    def rename_video(self, index, new_title):
        video = self.provider.get_video(index)
        self.database.change_video_file_title(video, new_title)
        self.provider.on_properties_modified(
            ("filename", "file_title") + (() if video.meta_title else ("meta_title",))
        )
        self.provider.load()
        return {
            "filename": to_json_value(video.filename),
            "file_title": video.file_title,
        }

    def count_prop_values(self, name, video_indices):
        prop_type = self.database.get_prop_type(name)
        value_to_count = {}
        nb_videos = 0
        video_indices = set(video_indices)
        for video in self.provider.get_view():
            if video.video_id in video_indices:
                nb_videos += 1
                if prop_type.multiple:
                    values = video.properties.get(prop_type.name, [])
                elif prop_type.name in video.properties:
                    values = [video.properties[prop_type.name]]
                else:
                    values = []
                for value in values:
                    value_to_count[value] = value_to_count.get(value, 0) + 1
        assert len(video_indices) == nb_videos
        return sorted(value_to_count.items())

    def edit_property_for_videos(
        self, name, video_indices, values_to_add, values_to_remove
    ):
        self.database.edit_property_for_videos(
            name, video_indices, values_to_add, values_to_remove
        )

    # Database properties features.

    def get_prop_types(self):
        props = sorted(self.database.get_prop_types(), key=lambda prop: prop.name)
        return [prop.to_json() for prop in props]

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

    def fill_property_with_terms(self, prop_name, only_empty=False):
        self.database.fill_property_with_terms(
            self.provider.get_all_videos(), prop_name, only_empty
        )
        self.provider.on_properties_modified([prop_name])

    def delete_property_value(self, name, values):
        modified = self.database.delete_property_value(
            self.provider.get_all_videos(), name, values
        )
        if modified:
            self.provider.on_properties_modified([name])
        return modified

    def edit_property_value(self, name, old_values, new_value):
        if self.database.edit_property_value(
            self.provider.get_all_videos(), name, old_values, new_value
        ):
            self.provider.on_properties_modified([name])

    def move_property_value(self, old_name, values, new_name):
        if self.database.move_property_value(
            self.provider.get_all_videos(), old_name, values, new_name
        ):
            self.provider.on_properties_modified((old_name, new_name))

    def set_video_properties(self, index, properties):
        self.provider.on_properties_modified(
            self.database.set_video_properties(
                self.provider.get_video(index), properties
            )
        )

    # Property multi-selection and concatenation features.

    def classifier_select_group(self, group_id):
        print("classifier select group", group_id)
        prop_name = self.provider.grouping_layer.get_grouping().field[1:]
        path = self.provider.classifier_layer.get_path()
        value = self.provider.classifier_layer.get_group_value(group_id)
        new_path = path + [value]
        self.provider.classifier_layer.set_path(new_path)
        self.provider.group_layer.set_group_id(0)
        self.provider.on_properties_modified([prop_name])

    def classifier_select_group_by_value(self, field_value):
        print("classifier select group by value", field_value)
        group_id = self.provider.grouping_layer.get_group_id(field_value)
        self.provider.classifier_layer.set_path([])
        self.provider.classifier_layer.run()
        self.classifier_select_group(group_id)

    def classifier_back(self):
        print("classifier back")
        prop_name = self.provider.grouping_layer.get_grouping().field[1:]
        path = self.provider.classifier_layer.get_path()
        self.provider.classifier_layer.set_path(path[:-1])
        self.provider.group_layer.set_group_id(0)
        self.provider.on_properties_modified([prop_name])

    def classifier_reverse(self):
        path = list(reversed(self.provider.classifier_layer.get_path()))
        self.provider.classifier_layer.set_path(path)
        return path

    def classifier_concatenate_path(self, to_property):
        path = self.provider.classifier_layer.get_path()
        from_property = self.provider.grouping_layer.get_grouping().field[1:]
        if self.database.move_concatenated_prop_val(
            self.provider.get_all_videos(), path, from_property, to_property
        ):
            self.provider.classifier_layer.set_path([])
            self.provider.group_layer.set_group_id(0)
            self.provider.on_properties_modified([from_property, to_property])
