from typing import Optional

from pysaurus.core.components import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.database.properties import PropType
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

    def get_info_and_videos(self, page_size, page_number, fields, video_indices=()):
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
            for index in range(start, end):
                video = view[index]
                js = {field: to_json_value(getattr(video, field)) for field in fields}
                js["exists"] = video.exists()
                js["hasThumbnail"] = video.thumbnail_path.exists()
                js["local_id"] = index
                videos.append(js)
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
        try:
            self.database.change_video_file_title(video, new_title)
            self.provider.on_properties_modified(
                ("filename", "file_title")
                + (() if video.meta_title else ("meta_title",))
            )
            self.provider.load()
            return {
                "filename": to_json_value(video.filename),
                "file_title": video.file_title,
            }
        except OSError as exc:
            return {"error": str(exc)}

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
        prop_type = self.database.get_prop_type(name)
        nb_videos = 0
        if prop_type.multiple:
            values_to_add = prop_type(values_to_add)
            values_to_remove = prop_type(values_to_remove)
        else:
            assert len(values_to_add) < 2
            values_to_add = [prop_type(value) for value in values_to_add]
            values_to_remove = {prop_type(value) for value in values_to_remove}
        video_indices = set(video_indices)
        for video in self.provider.get_view():
            if video.video_id in video_indices:
                nb_videos += 1
                if prop_type.multiple:
                    values = set(video.properties.get(prop_type.name, ()))
                    values.difference_update(values_to_remove)
                    values.update(values_to_add)
                    if values:
                        video.properties[prop_type.name] = prop_type(values)
                    elif prop_type.name in video.properties:
                        del video.properties[prop_type.name]
                else:
                    if (
                        values_to_remove
                        and prop_type.name in video.properties
                        and video.properties[prop_type.name] in values_to_remove
                    ):
                        del video.properties[prop_type.name]
                    if values_to_add:
                        video.properties[prop_type.name] = values_to_add[0]
        assert len(video_indices) == nb_videos
        self.database.save()

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
        prop_type = self.database.get_prop_type(prop_name)
        assert prop_type.multiple
        assert prop_type.type is str
        for video in self.provider.get_all_videos():
            if only_empty and video.properties.get(prop_name, None):
                continue
            values = video.terms(as_set=True)
            values.update(video.properties.get(prop_name, ()))
            video.properties[prop_name] = prop_type(values)
        self.database.save()
        self.provider.on_properties_modified([prop_name])

    def delete_property_value(self, name, values):
        assert isinstance(values, list), type(values)
        print("delete property value", name, values)
        values = set(values)
        modified = []
        prop_type = self.database.get_prop_type(name)
        if prop_type.multiple:
            prop_type.validate(values)
            for video in self.provider.get_all_videos():
                if name in video.properties and video.properties[name]:
                    new_values = set(video.properties[name])
                    len_before = len(new_values)
                    new_values = new_values - values
                    len_after = len(new_values)
                    if len_before > len_after:
                        video.properties[name] = prop_type(new_values)
                        modified.append(video)
        else:
            for value in values:
                prop_type.validate(value)
            for video in self.provider.get_all_videos():
                if name in video.properties and video.properties[name] in values:
                    del video.properties[name]
                    modified.append(video)
        if modified:
            self.database.save()
            self.provider.on_properties_modified([name])
        return modified

    def edit_property_value(self, name, old_values, new_value):
        print("edit property value", name, old_values, new_value)
        old_values = set(old_values)
        modified = False
        prop_type = self.database.get_prop_type(name)
        if prop_type.multiple:
            prop_type.validate(old_values)
            prop_type.validate([new_value])
            for video in self.provider.get_all_videos():
                if name in video.properties and video.properties[name]:
                    new_values = set(video.properties[name])
                    len_before = len(new_values)
                    new_values = new_values - old_values
                    len_after = len(new_values)
                    if len_before > len_after:
                        new_values.add(new_value)
                        video.properties[name] = prop_type(new_values)
                        modified = True
        else:
            for old_value in old_values:
                prop_type.validate(old_value)
            prop_type.validate(new_value)
            for video in self.provider.get_all_videos():
                if name in video.properties and video.properties[name] in old_values:
                    video.properties[name] = new_value
                    modified = True
        if modified:
            self.database.save()
            self.provider.on_properties_modified([name])

    def move_property_value(self, old_name, values, new_name):
        assert len(values) == 1, values
        value = values[0]
        print("move property value", old_name, new_name, value)
        prop_type = self.database.get_prop_type(new_name)
        prop_type.validate([value] if prop_type.multiple else value)
        videos = self.delete_property_value(old_name, [value])
        if prop_type.multiple:
            for video in videos:
                new_values = set(video.properties.get(new_name, ()))
                new_values.add(value)
                video.properties[new_name] = prop_type(new_values)
        else:
            for video in videos:
                video.properties[new_name] = value
        if videos:
            self.database.save()
            self.provider.on_properties_modified((old_name, new_name))

    def set_video_properties(self, index, properties):
        modified = self.database.set_video_properties(
            self.provider.get_video(index), properties
        )
        self.provider.on_properties_modified(modified)

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
        from_prop_type = self.database.get_prop_type(from_property)
        to_prop_type = self.database.get_prop_type(to_property)
        assert from_prop_type.multiple
        assert to_prop_type.type is str
        from_prop_type.validate(path)
        modified = []

        for video in self.provider.get_all_videos():
            if from_property in video.properties and video.properties[from_property]:
                new_values = set(video.properties[from_property])
                len_before = len(new_values)
                new_values = new_values - set(path)
                if len_before == len(new_values) + len(path):
                    video.properties[from_property] = from_prop_type(new_values)
                    modified.append(video)

        new_value = " ".join(str(value) for value in path)
        if to_prop_type.multiple:
            for video in modified:
                new_values = set(video.properties.get(to_property, ()))
                new_values.add(new_value)
                video.properties[to_property] = to_prop_type(new_values)
        else:
            for video in modified:
                video.properties[to_property] = to_prop_type(new_value)

        if modified:
            self.database.save()
            self.provider.classifier_layer.set_path([])
            self.provider.group_layer.set_group_id(0)
            self.provider.on_properties_modified([from_property, to_property])
