import os
import subprocess

from other.legacy.video_raptor_cpp.abstract_video_raptor import AbstractVideoRaptor
from other.legacy.video_raptor_cpp.bin.symbols import RUN_VIDEO_RAPTOR_BATCH
from pysaurus.application import exceptions
from pysaurus.core.abstract_notifier import AbstractNotifier
from pysaurus.core.components import AbsolutePath
from pysaurus.core.custom_json_parser import parse_json
from pysaurus.core.parallelization import Job


class VideoRaptor(AbstractVideoRaptor):
    __slots__ = ()

    @classmethod
    def _job_video_to_json(cls, job):
        notifier: AbstractNotifier
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
                    notifier.progress(cls.collect_video_info, step, job_count, job_id)
        program_errors = process.stderr.read().decode().strip()
        if not end and program_errors:
            raise exceptions.VideoToJsonError(program_errors)
        assert nb_read == job_count
        notifier.progress(cls.collect_video_info, job_count, job_count, job_id)
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