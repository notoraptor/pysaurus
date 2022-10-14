import sys
from typing import Optional

from pysaurus.application.application import Application
from pysaurus.core import notifications
from pysaurus.core.components import Duration, FileSize
from pysaurus.core.functions import compute_nb_pages
from pysaurus.database.database import Database
from pysaurus.database.properties import PropType
from pysaurus.database.video_features import VideoFeatures
from pysaurus.database.viewport.layers.source_layer import SourceLayer
from pysaurus.database.viewport.video_provider import VideoProvider
from pysaurus.language.default_language import language_to_dict


class FeatureAPI:
    PYTHON_DEFAULT_SOURCES = SourceLayer.DEFAULT_SOURCE_DEF
    PYTHON_APP_NAME = Application.app_name
    PYTHON_HAS_EMBEDDED_PLAYER = False
    PYTHON_FEATURE_COMPARISON = True

    def __init__(self, notifier):
        self.notifier = notifier
        self.application = Application(self.notifier)
        self.database: Optional[Database] = None
        self.provider: Optional[VideoProvider] = None
        self.PYTHON_LANG = language_to_dict(self.application.lang)

    # Utilities.

    def _parse_video_selector(self, selector: dict, return_videos=False):
        if selector["all"]:
            exclude = set(selector["exclude"])
            output = [
                (video if return_videos else video.video_id)
                for video in self.provider.get_view()
                if video.video_id not in exclude
            ]
        else:
            include = set(selector["include"])
            output = (
                [
                    video
                    for video in self.provider.get_view()
                    if video.video_id in include
                ]
                if return_videos
                else include
            )
        return output

    # Constant getters.

    def get_constants(self):
        return {
            key: getattr(self, key) for key in dir(self) if key.startswith("PYTHON_")
        }

    def _list_databases(self):
        return [{"name": name} for name in self.application.get_database_names()]

    def list_languages(self):
        return [
            {"name": path.title, "path": str(path)}
            for path in self.application.get_language_paths()
        ]

    def get_app_state(self):
        return {"languages": self.list_languages(), "databases": self._list_databases()}

    def set_language(self, name):
        return language_to_dict(self.application.open_language_from_name(name))

    # Provider getters.

    def backend(self, callargs, page_size, page_number, selector=None):
        prev_sources = self.provider.source_layer.get_sources()
        prev_grouping = self.provider.grouping_layer.get_grouping()
        prev_path = self.provider.classifier_layer.get_path()
        prev_group_id = self.provider.group_layer.get_group_id()
        prev_search = self.provider.search_layer.get_search()

        if callargs:
            ret = getattr(self, callargs[0])(*callargs[1:])
            if ret is not None:
                print("Ignored value returned by", callargs, file=sys.stderr)
                print(type(ret), file=sys.stderr)

        # Backend state.
        real_nb_videos = len(self.provider.get_view())
        if selector:
            view = self._parse_video_selector(selector, return_videos=True)
        else:
            view = self.provider.get_view()
        nb_videos = len(view)
        nb_pages = compute_nb_pages(nb_videos, page_size)
        videos = []
        group_def = self.provider.get_group_def()
        if nb_videos:
            page_number = min(max(0, page_number), nb_pages - 1)
            start = page_size * page_number
            end = min(start + page_size, nb_videos)
            videos = [VideoFeatures.to_json(view[index]) for index in range(start, end)]
            if group_def and group_def["field"] == "similarity_id":
                group_def["common"] = VideoFeatures.get_common_fields(view)

        sources = self.provider.source_layer.get_sources()
        grouping = self.provider.grouping_layer.get_grouping()
        path = self.provider.classifier_layer.get_path()
        group_id = self.provider.group_layer.get_group_id()
        search = self.provider.search_layer.get_search()

        provider_changed = (
            prev_sources != sources
            or prev_grouping != grouping
            or prev_path != path
            or prev_group_id != group_id
            or prev_search != search
        )

        prop_types = self.get_prop_types()
        extra = {}
        db_message = self.database.flush_message()
        if db_message:
            extra["status"] = db_message
        return {
            "pageSize": page_size,
            "pageNumber": page_number,
            "nbVideos": nb_videos,
            "realNbVideos": real_nb_videos,
            "totalNbVideos": len(self.provider.source_layer.videos()),
            "nbPages": nb_pages,
            "validSize": str(FileSize(sum(video.file_size for video in view))),
            "validLength": str(
                Duration(
                    sum(video.raw_microseconds for video in view if video.readable)
                )
            ),
            "notFound": all("not_found" in source for source in sources),
            "sources": sources,
            "groupDef": group_def,
            "searchDef": self.provider.get_search_def(),
            "sorting": self.provider.sort_layer.get_sorting(),
            "videos": videos,
            "path": path,
            "properties": prop_types,
            "definitions": {prop["name"]: prop for prop in prop_types},
            "database": {
                "name": self.database.name,
                "folders": [str(path) for path in sorted(self.database.video_folders)],
            },
            "viewChanged": provider_changed,
            **extra,
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

    # stable
    def classifier_reverse(self):
        path = list(reversed(self.provider.classifier_layer.get_path()))
        self.provider.classifier_layer.set_path(path)
        return path

    # Database actions without modifications.

    def choose_random_video(self):
        video = self.provider.get_random_found_video()
        self.provider.source_layer.reset_parameters()
        self.provider.grouping_layer.reset_parameters()
        self.provider.classifier_layer.reset_parameters()
        self.provider.group_layer.reset_parameters()
        self.set_search(str(video.video_id), "id")
        return video

    def open_random_video(self):
        return str(self.choose_random_video().filename.open())

    def open_random_player(self):
        raise NotImplementedError()

    def open_video(self, video_id):
        self.database.get_video_filename(video_id).open()

    def open_containing_folder(self, video_id):
        return str(self.database.get_video_filename(video_id).locate_file())

    # Database getters.

    def get_prop_types(self):
        props = sorted(self.database.get_prop_types(), key=lambda prop: prop.name)
        return [prop.describe() for prop in props]

    def count_prop_values(self, name, selector):
        value_to_count = self.database.count_property_values(
            name, self._parse_video_selector(selector)
        )
        return sorted(value_to_count.items())

    # Database setters.

    def set_video_folders(self, paths):
        self.database.set_folders(paths)
        self.provider.refresh()

    def rename_database(self, name):
        self.database.rename(name)

    def prop_to_lowercase(self, prop_name):
        self.database.prop_to_lowercase(prop_name)

    def prop_to_uppercase(self, prop_name):
        self.database.prop_to_uppercase(prop_name)

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

    def dismiss_similarity(self, video_id):
        self.database.set_similarity(video_id, -1)

    def reset_similarity(self, video_id):
        self.database.set_similarity(video_id, None)

    def delete_video(self, video_id):
        self.database.delete_video(video_id)

    def rename_video(self, video_id, new_title):
        self.database.change_video_file_title(video_id, new_title)
        self.provider.refresh()

    def edit_property_for_videos(self, name, selector, to_add, to_remove):
        self.database.edit_property_for_videos(
            name, self._parse_video_selector(selector), to_add, to_remove
        )

    def set_video_properties(self, video_id, properties):
        self.database.set_video_properties(video_id, properties)

    def fill_property_with_terms(self, prop_name, only_empty=False):
        self.database.fill_property_with_terms(
            self.provider.get_all_videos(), prop_name, only_empty
        )

    def delete_property_value(self, name, values):
        self.database.delete_property_value(
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

    def set_video_moved(self, from_id, to_id):
        self.database.move_video_entry(from_id, to_id)

    def confirm_unique_moves(self):
        return self.database.confirm_unique_moves()
