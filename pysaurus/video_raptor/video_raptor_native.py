import os
import subprocess

from pysaurus.application import exceptions
from pysaurus.bin.symbols import RUN_VIDEO_RAPTOR_BATCH, RUN_VIDEO_RAPTOR_THUMBNAILS
from pysaurus.core.components import AbsolutePath
from pysaurus.core.custom_json_parser import parse_json
from pysaurus.core.job_notifications import notify_job_progress
from pysaurus.core.parallelization import Job
from pysaurus.video_raptor.abstract_video_raptor import AbstractVideoRaptor


class VideoRaptor(AbstractVideoRaptor):
    __slots__ = ()

    @classmethod
    def _job_video_to_json(cls, job):
        input_file_name, output_file_name, job_count, job_id, notifier = job

        nb_read = 0
        nb_loaded = 0
        end = False
        input_file_path = AbsolutePath.ensure(input_file_name)
        output_file_path = AbsolutePath.ensure(output_file_name)
        assert input_file_path.isfile()
        if output_file_path.exists():
            output_file_path.delete()

        env = os.environ.copy()
        process = subprocess.Popen(
            [RUN_VIDEO_RAPTOR_BATCH.path, input_file_name, output_file_name],
            env=env,
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
                    notify_job_progress(
                        notifier, cls.collect_video_info, job_id, step, job_count
                    )
        program_errors = process.stderr.read().decode().strip()
        if not end and program_errors:
            raise exceptions.VideoToJsonError(program_errors)
        assert nb_read == job_count
        notify_job_progress(
            notifier, cls.collect_video_info, job_id, job_count, job_count
        )
        return nb_loaded

    @classmethod
    def _job_video_thumbnails_to_json(cls, job):
        input_file_name, output_file_name, job_count, job_id, notifier = job

        nb_read = 0
        nb_loaded = 0
        end = False
        input_file_path = AbsolutePath.ensure(input_file_name)
        output_file_path = AbsolutePath.ensure(output_file_name)
        assert input_file_path.isfile()
        if output_file_path.exists():
            output_file_path.delete()

        env = os.environ.copy()
        process = subprocess.Popen(
            [RUN_VIDEO_RAPTOR_THUMBNAILS.path, input_file_name, output_file_name],
            env=env,
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
                    notify_job_progress(
                        notifier, cls.collect_video_thumbnails, job_id, step, job_count
                    )
        program_errors = process.stderr.read().decode().strip()
        if not end and program_errors:
            raise exceptions.VideoThumbnailsToJsonError(program_errors)
        assert nb_read == job_count
        notify_job_progress(
            notifier, cls.collect_video_thumbnails, job_id, job_count, job_count
        )
        return nb_loaded

    def collect_video_info(self, job: Job) -> list:
        database_folder, notifier = job.args
        list_file_path = AbsolutePath.file_path(database_folder, str(job.id), "list")
        json_file_path = AbsolutePath.file_path(database_folder, str(job.id), "json")

        with open(list_file_path.path, "wb") as file:
            for file_name in job.batch:
                file.write(f"{file_name}\n".encode())

        self._job_video_to_json(
            (list_file_path.path, json_file_path.path, len(job.batch), job.id, notifier)
        )
        assert json_file_path.isfile()
        arr = parse_json(json_file_path)
        # assert len(arr) == count, (len(arr), count)
        list_file_path.delete()
        json_file_path.delete()
        return arr

    def collect_video_thumbnails(self, job: Job) -> list:
        db_folder, thumb_folder, notifier = job.args
        list_file_path = AbsolutePath.file_path(db_folder, job.id, "thumbnails.list")
        json_file_path = AbsolutePath.file_path(db_folder, job.id, "thumbnails.json")

        with open(list_file_path.path, "wb") as file:
            for file_path, thumb_name in job.batch:
                file.write(f"{file_path}\t{thumb_folder}\t{thumb_name}\t\n".encode())

        nb_loaded = self._job_video_thumbnails_to_json(
            (list_file_path.path, json_file_path.path, len(job.batch), job.id, notifier)
        )
        assert json_file_path.isfile()
        arr = parse_json(json_file_path)
        assert arr[-1] is None
        arr.pop()
        assert nb_loaded + len(arr) == len(job.batch)
        list_file_path.delete()
        json_file_path.delete()
        return arr
