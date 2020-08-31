import multiprocessing
import queue
import threading
import time
import traceback
from typing import Optional

from pysaurus.core.database.api import API
from pysaurus.core.database.notifications import DatabaseReady
from pysaurus.core.database.properties import PropType
from pysaurus.core.database.video_provider import VideoProvider, SOURCE_TREE
from pysaurus.core.functions import launch_thread
from pysaurus.core.notification import Notification
from pysaurus.interface.common.parallel_notifier import ParallelNotifier
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


class GuiAPI:
    JSON_INTEGER_MIN = -2 ** 31
    JSON_INTEGER_MAX = 2 ** 31 - 1

    def __init__(self):
        self.multiprocessing_manager = multiprocessing.Manager()
        self.notifier = ParallelNotifier(self.multiprocessing_manager.Queue())

        self.monitor_thread = None  # type: Optional[threading.Thread]
        self.db_loading_thread = None  # type: Optional[threading.Thread]
        self.threads_stop_flag = False

        self.api = None  # type: Optional[API]
        self.provider = None  # type: Optional[VideoProvider]

        self.__update_on_load = True

    def close_app(self):
        self.threads_stop_flag = True
        if self.monitor_thread:
            self.monitor_thread.join()
        if self.db_loading_thread:
            self.db_loading_thread.join()

    def load_database(self, update=True):
        self.__update_on_load = update
        # Launch monitor thread.
        self.monitor_thread = launch_thread(self._monitor_notifications)
        # Then launch database loading thread.
        self.db_loading_thread = launch_thread(self._load_database)

    def update_database(self):
        assert not self.monitor_thread
        assert not self.db_loading_thread
        self.monitor_thread = launch_thread(self._monitor_notifications)
        self.db_loading_thread = launch_thread(self._update_database)

    def set_sorting(self, sorting):
        self.provider.set_sort(sorting)

    def get_group_def(self):
        return self.provider.get_group_def()

    def get_search_def(self):
        return self.provider.get_search_def()

    def get_sorting(self):
        return self.provider.get_sorting()

    def set_search(self, search_text: str, search_type: str):
        self.provider.set_search(search_text, search_type)

    def get_videos(self, page_size, page_number, fields):
        videos = []
        nb_videos = self._count_videos()
        if nb_videos:
            nb_pages = self._count_pages(page_size)
            if page_number < 0:
                page_number = 0
            if page_number >= nb_pages:
                page_number = nb_pages - 1
            start = page_size * page_number
            end = min(start + page_size, nb_videos)
            for index in range(start, end):
                video = self.provider.get_video(index)
                js = {field: self._to_json_value(getattr(video, field)) for field in fields}
                js['exists'] = video.exists()
                js['hasThumbnail'] = video.thumbnail_path.exists()
                js['local_id'] = index
                videos.append(js)
        return {'videos' : videos, 'pageNumber': page_number}

    def get_info(self, page_size):
        group_def = self.get_group_def()
        return {
            'nbVideos': self._count_videos(),
            'nbPages': self._count_pages(page_size),
            'validSize': self._valid_size(),
            'validLength': self._valid_length(),
            'nbGroups': self._count_groups(),
            'notFound': self.provider.all_not_found(),
            'sources': self.get_sources(),
            'groupDef': group_def,
            'searchDef': self.get_search_def(),
            'sorting': self.get_sorting(),
            'sourceTree': self.get_source_tree()
        }

    def get_info_and_videos(self, page_size, page_number, fields):
        info = self.get_info(page_size)
        info.update(self.get_videos(page_size, page_number, fields))
        info['properties'] = self.get_prop_types()
        return info

    def open_video(self, index):
        try:
            return str(self.provider.get_video(index).filename.open())
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
            self.api.database.change_video_file_title(video, new_title)
            self.provider.check_group()
            return {'filename': self._to_json_value(video.filename), 'file_title': video.file_title}
        except OSError as exc:
            return {'error': str(exc)}

    def group_videos(self, field, sorting=None, reverse=None, allow_singletons=None, allow_multiple=None):
        self.provider.set_groups(field, sorting, reverse, allow_singletons, allow_multiple)

    def set_group(self, index):
        self.provider.set_group(index)

    def set_group_by_value(self, value):
        self.provider.set_group_by_value(value)

    def get_source_tree(self):
        # TODO unreable videos cannot be displayed yet, as they are incomplete VideoState (not Video) objects.
        tree = SOURCE_TREE.copy()
        del tree['unreadable']
        return tree

    def get_sources(self):
        return self.provider.get_sources()

    def get_source_info(self):
        return {
            'tree': self.get_source_tree(),
            'sources': self.provider.get_sources()
        }

    def set_sources(self, paths):
        self.provider.set_source(paths)

    def add_prop_type(self, prop_name, prop_type, prop_default, prop_multiple):
        if prop_type == 'float':
            if isinstance(prop_default, list):
                prop_default = [float(element) for element in prop_default]
            else:
                prop_default = float(prop_default)
        self.api.database.add_prop_type(PropType(prop_name, prop_default, prop_multiple))
        return self.get_prop_types()

    def get_prop_types(self):
        props = sorted(self.api.database.get_prop_types(), key=lambda prop: prop.name)
        return [prop.to_json() for prop in props]

    def delete_prop_type(self, name):
        self.api.database.remove_prop_type(name)
        return self.get_prop_types()

    def set_video_properties(self, index, properties):
        modified = self.api.database.set_video_properties(self.provider.get_video(index), properties)
        self.provider.on_properties_modified(modified)

    def fill_property_with_terms(self, prop_name):
        db = self.api.database
        prop_type = db.get_prop_type(prop_name)
        assert prop_type.multiple
        assert prop_type.type is str
        for video in self.provider.videos():
            values = video.terms(as_set=True)
            values.update(video.properties.get(prop_name, ()))
            video.set_property(prop_name, prop_type(values))
        db.save()
        self.provider.on_properties_modified([prop_name])

    def delete_property_value(self, name, value):
        print('delete property value', name, value)
        modified = []
        prop_type = self.api.database.get_prop_type(name)
        if prop_type.multiple:
            prop_type.validate([value])
            for video in self.provider.videos():
                if name in video.properties and video.properties[name]:
                    new_values = set(video.properties[name])
                    if value in new_values:
                        new_values.remove(value)
                        video.properties[name] = prop_type(new_values)
                        modified.append(video)
        else:
            prop_type.validate(value)
            for video in self.provider.videos():
                if name in video.properties and video.properties[name] == value:
                    del video.properties[name]
                    modified.append(video)
        if modified:
            self.api.database.save()
            self.provider.on_properties_modified([name])
        return modified

    def edit_property_value(self, name, old_value, new_value):
        print('edit property value', name, old_value, new_value)
        modified = False
        prop_type = self.api.database.get_prop_type(name)
        if prop_type.multiple:
            prop_type.validate([old_value])
            prop_type.validate([new_value])
            for video in self.provider.videos():
                if name in video.properties and video.properties[name]:
                    new_values = set(video.properties[name])
                    if old_value in new_values:
                        new_values.remove(old_value)
                        new_values.add(new_value)
                        video.properties[name] = prop_type(new_values)
                        modified = True
        else:
            prop_type.validate(old_value)
            prop_type.validate(new_value)
            for video in self.provider.videos():
                if name in video.properties and video.properties[name] == old_value:
                    video.properties[name] = new_value
                    modified = True
        if modified:
            self.api.database.save()
            self.provider.on_properties_modified([name])

    def move_property_value(self, old_name, value, new_name):
        print('move property value', old_name, new_name, value)
        prop_type = self.api.database.get_prop_type(new_name)
        prop_type.validate([value] if prop_type.multiple else value)
        videos = self.delete_property_value(old_name, value)
        if prop_type.multiple:
            for video in videos:
                new_values = set(video.properties.get(new_name, ()))
                new_values.add(value)
                video.properties[new_name] = prop_type(new_values)
        else:
            for video in videos:
                video.properties[new_name] = value
        if videos:
            self.api.database.save()
            self.provider.on_properties_modified((old_name, new_name))

    def _count_videos(self):
        return self.provider.count()

    def _count_pages(self, page_size):
        assert page_size > 0
        count = self._count_videos()
        return (count // page_size) + bool(count % page_size)

    def _count_groups(self):
        return self.provider.count_groups()

    def _valid_size(self):
        return str(self.provider.get_view_file_size())

    def _valid_length(self):
        return str(self.provider.get_view_duration())

    def _get_group_field_value(self):
        return self._to_json_value(self.provider.get_group_field_value())

    def _load_videos(self):
        if self.provider:
            self.provider.load()
        else:
            self.provider = VideoProvider(self.api.database)

    def _monitor_notifications(self):
        print('Monitoring notifications ...')
        while True:
            if self.threads_stop_flag:
                break
            try:
                notification = self.notifier.queue.get_nowait()
                self._notify(notification)
                if isinstance(notification, DatabaseReady):
                    break
            except queue.Empty:
                time.sleep(1 / 100)
            except Exception as exc:
                print('Exception while sending notification:')
                traceback.print_tb(exc.__traceback__)
                print(type(exc).__name__)
                print(exc)
                print()
        self.monitor_thread = None
        print('End monitoring.')

    def _notify(self, notification):
        # type: (Notification) -> None
        print(notification)
        self._call_gui_function('__notify', {
            'name': notification.get_name(),
            'notification': notification.to_dict(),
            'message': str(notification)
        })

    def _call_gui_function(self, function_name, *parameters):
        # to override.
        pass

    def _load_database(self):
        update = self.__update_on_load
        self.__update_on_load = True
        self.api = API(TEST_LIST_FILE_PATH,
                       update=update,
                       notifier=self.notifier,
                       ensure_miniatures=False,
                       reset=False)
        self._load_videos()
        self.notifier.notify(DatabaseReady())
        self.db_loading_thread = None
        print('End loading database.')

    def _update_database(self):
        self.api.update(ensure_miniatures=True)
        self._load_videos()
        self.notifier.notify(DatabaseReady())
        self.db_loading_thread = None
        print('End updating database.')

    def _to_json_value(self, value):
        if isinstance(value, (tuple, list, set)):
            return [self._to_json_value(element) for element in value]
        if isinstance(value, dict):
            return {self._to_json_value(key): self._to_json_value(element) for key, element in value.items()}
        if isinstance(value, (str, float, bool, type(None))):
            return value
        if isinstance(value, int) and self.JSON_INTEGER_MIN <= value <= self.JSON_INTEGER_MAX:
            return value
        return str(value)

    def _json_error(self, message):
        return {'status': -1, 'message': message}

    def _json_ok(self):
        return {'status': 0}
