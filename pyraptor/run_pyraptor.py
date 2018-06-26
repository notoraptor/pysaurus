import os
import sys
import traceback
import concurrent.futures
from pyraptor import videoraptor
from pyraptor.absolute_path import AbsolutePath
from pyraptor import utils
from pyraptor.profiling import Profiler


def collect_files(folder_path: AbsolutePath, collector: dict):
    print('#COLLECTING', folder_path)
    for file_name in folder_path.listdir():
        path = AbsolutePath.join(folder_path, file_name)
        if path.isdir():
            collect_files(path, collector)
        elif utils.is_valid_video_filename(path.path):
            collector.setdefault(folder_path, []).append(path)


def collect_file(file_path: AbsolutePath, collector: dict):
    if utils.is_valid_video_filename(file_path.path):
        collector.setdefault(file_path.get_directory(), []).append(file_path)
        return True
    return False


def report_collection(collection: dict):
    print('%d\tTOTAL' % sum(len(file_names) for file_names in collection.values()))
    for path in sorted(collection.keys()):
        print('%d\t%s' % (len(collection[path]), path))


def extract_info(job):
    tasks, job_id = job
    _n_reads = videoraptor.get_n_reads()
    _videos = []
    _messages = []
    cursor = 0
    count_tasks = len(tasks)
    while cursor < count_tasks:
        print('CURSOR[%s]' % job_id, cursor)
        try:
            res, local_messages, local_videos = videoraptor.get_video_details(tasks[cursor:(cursor + _n_reads)])
            if not res:
                print('[%s] C call returned False.' % job_id, file=sys.stderr)
            else:
                _videos.append(local_videos)
                _messages.append(local_messages)
            _messages.append(videoraptor.pop_logger())
        except Exception as exc:
            print('Exception occurred', file=sys.stdout)
            traceback.print_tb(exc.__traceback__, file=sys.stdout)
            print(exc, file=sys.stdout)
        cursor += _n_reads
    return _videos, _messages


def main():
    list_file_path = os.path.join('..', '.local', 'test_folder.log')
    files = {}
    if not os.path.exists(list_file_path) or not os.path.isfile(list_file_path):
        raise Exception('Invalid file path ' + list_file_path)
    with open(list_file_path) as list_file:
        for line in list_file:
            line = line.strip()
            if line and line[0] != '#':
                path = AbsolutePath(line)
                if not path.exists():
                    print('#NOT_FOUND', path)
                elif path.isdir():
                    collect_files(path, files)
                elif not collect_file(path, files):
                    print('#IGNORED', path)
    report_collection(files)

    videos = []
    messages = []
    all_files = []
    short_to_long = {}
    for folder_files in files.values():
        for file_name in folder_files:
            short_name = utils.get_convenient_os_path(file_name.path)
            short_to_long[short_name] = file_name
            all_files.append(short_name)
    cpu_count = os.cpu_count()
    jobs = utils.dispatch_tasks(all_files, cpu_count, 0)

    with Profiler(exit_message='Files parsed:'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(extract_info, jobs))
    for result in results:
        print(len(result[0]), len(result[1]))


if __name__ == '__main__':
    main()
