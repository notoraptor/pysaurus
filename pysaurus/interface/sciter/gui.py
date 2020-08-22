import multiprocessing
import threading
from typing import Optional

import sciter

from pysaurus.core.database.api import API
from pysaurus.core.database.video_provider import VideoProvider
from pysaurus.interface.common.gui_api import GuiAPI
from pysaurus.interface.common.parallel_notifier import ParallelNotifier


class Frame(GuiAPI, sciter.Window):

    def __init__(self):
        sciter.Window.__init__(self, ismain=True, uni_theme=True)
        GuiAPI.__init__(self)
        self.load_file('web/index.html')
        self.expand()

    close_app = sciter.script(GuiAPI.close_app)
    load_database = sciter.script(GuiAPI.load_database)
    update_database = sciter.script(GuiAPI.update_database)
    set_sorting = sciter.script(GuiAPI.set_sorting)
    get_group_def = sciter.script(GuiAPI.get_group_def)
    get_search_def = sciter.script(GuiAPI.get_search_def)
    get_sorting = sciter.script(GuiAPI.get_sorting)
    set_search = sciter.script(GuiAPI.set_search)
    get_videos = sciter.script(GuiAPI.get_videos)
    open_video = sciter.script(GuiAPI.open_video)
    open_containing_folder = sciter.script(GuiAPI.open_containing_folder)
    open_random_video = sciter.script(GuiAPI.open_random_video)
    delete_video = sciter.script(GuiAPI.delete_video)
    rename_video = sciter.script(GuiAPI.rename_video)
    group_videos = sciter.script(GuiAPI.group_videos)
    set_group = sciter.script(GuiAPI.set_group)
    get_info = sciter.script(GuiAPI.get_info)
    get_source_tree = sciter.script(GuiAPI.get_source_tree)
    set_sources = sciter.script(GuiAPI.set_sources)
    get_sources = sciter.script(GuiAPI.get_sources)
    add_prop_type = sciter.script(GuiAPI.add_prop_type)
    get_prop_types = sciter.script(GuiAPI.get_prop_types)
    delete_prop_type = sciter.script(GuiAPI.delete_prop_type)

    def _call_gui_function(self, function_name, *parameters):
        return self.call_function(function_name, *parameters)


def main():
    # sciter.set_option(sciter.SCITER_RT_OPTIONS.SCITER_SET_SCRIPT_RUNTIME_FEATURES, 1)
    sciter.runtime_features()
    Frame().run_app()
    print('End')


if __name__ == '__main__':
    main()
