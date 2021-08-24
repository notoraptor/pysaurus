import os
import subprocess
from typing import List, Dict

from pysaurus.application import exceptions
from pysaurus.bin.symbols import RUN_VIDEO_RAPTOR_BATCH, RUN_VIDEO_RAPTOR_THUMBNAILS
from pysaurus.core import functions, constants
from pysaurus.core.components import AbsolutePath
from pysaurus.core.database.video_runtime_info import VideoRuntimeInfo
from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.modules import FileSystem, ImageUtils
from pysaurus.core.notifications import JobNotifications


def _collect_videos_info(folder: str, files: Dict[AbsolutePath, VideoRuntimeInfo]):
    entry: os.DirEntry
    for entry in FileSystem.scandir(folder):
        if entry.is_dir():
            _collect_videos_info(entry.path, files)
        elif (
            functions.get_file_extension(entry.name)
            in constants.VIDEO_SUPPORTED_EXTENSIONS
        ):
            stat = entry.stat()
            files[AbsolutePath(entry.path)] = VideoRuntimeInfo(
                size=stat.st_size,
                mtime=stat.st_mtime,
                driver_id=stat.st_dev,
                is_file=True,
            )


def job_collect_videos_info(job):
    # type: (List) -> Dict[AbsolutePath, VideoRuntimeInfo]
    files = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    for path in job[0]:  # type: AbsolutePath
        if path.isdir():
            _collect_videos_info(path.path, files)
        elif path.extension in constants.VIDEO_SUPPORTED_EXTENSIONS:
            stat = FileSystem.stat(path.path)
            files[path] = VideoRuntimeInfo(
                size=stat.st_size,
                mtime=stat.st_mtime,
                driver_id=stat.st_dev,
                is_file=True,
            )
    return files


def job_video_to_json(job):
    jobn: JobNotifications
    input_file_name, output_file_name, job_count, job_id, jobn = job

    nb_read = 0
    nb_loaded = 0
    end = False
    input_file_path = AbsolutePath.ensure(input_file_name)
    output_file_path = AbsolutePath.ensure(output_file_name)
    assert input_file_path.isfile()
    if output_file_path.exists():
        output_file_path.delete()

    process = subprocess.Popen(
        [RUN_VIDEO_RAPTOR_BATCH.path, input_file_name, output_file_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    while True:
        line = process.stdout.readline().decode().strip()
        if not line and process.poll() is not None:
            break
        if line:
            if line.startswith("#"):
                if line.startswith("#count "):
                    nb_read = int(line[7:])
                elif line.startswith("#loaded "):
                    nb_loaded = int(line[8:])
                elif line == "#end":
                    end = True
            else:
                step = int(line)
                jobn.progress(job_id, step, job_count)
    program_errors = process.stderr.read().decode().strip()
    if not end and program_errors:
        raise exceptions.VideoToJsonError(program_errors)
    assert nb_read == job_count
    jobn.progress(job_id, job_count, job_count)
    return nb_loaded


def job_video_thumbnails_to_json(job):
    jobn: JobNotifications
    input_file_name, output_file_name, job_count, job_id, jobn = job

    nb_read = 0
    nb_loaded = 0
    end = False
    input_file_path = AbsolutePath.ensure(input_file_name)
    output_file_path = AbsolutePath.ensure(output_file_name)
    assert input_file_path.isfile()
    if output_file_path.exists():
        output_file_path.delete()

    process = subprocess.Popen(
        [RUN_VIDEO_RAPTOR_THUMBNAILS.path, input_file_name, output_file_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    while True:
        line = process.stdout.readline().decode().strip()
        if not line and process.poll() is not None:
            break
        if line:
            if line.startswith("#"):
                if line.startswith("#count "):
                    nb_read = int(line[7:])
                elif line.startswith("#loaded "):
                    nb_loaded = int(line[8:])
                elif line == "#end":
                    end = True
            else:
                step = int(line)
                jobn.progress(job_id, step, job_count)
    program_errors = process.stderr.read().decode().strip()
    if not end and program_errors:
        raise exceptions.VideoThumbnailsToJsonError(program_errors)
    assert nb_read == job_count
    jobn.progress(job_id, job_count, job_count)
    return nb_loaded


def job_generate_miniatures(job) -> List[Miniature]:
    jobn: JobNotifications
    thumbnails, job_id, jobn = job
    nb_videos = len(thumbnails)
    miniatures = []
    for i, (file_name, thumbnail_path) in enumerate(thumbnails):
        miniatures.append(
            Miniature.from_file_name(
                thumbnail_path.path, ImageUtils.DEFAULT_THUMBNAIL_SIZE, file_name.path
            )
        )
        if (i + 1) % 500 == 0:
            jobn.progress(job_id, i + 1, nb_videos)
    jobn.progress(job_id, nb_videos, nb_videos)
    return miniatures
