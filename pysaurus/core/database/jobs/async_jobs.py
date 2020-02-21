import asyncio
from pysaurus.core.components import AbsolutePath
from pysaurus.core.database import notifications
from pysaurus.core.components import System

if System.is_windows():
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def job_video_to_json(job):
    input_file_name, output_file_name, job_count, job_id, notifier = job

    nb_read = 0
    nb_loaded = 0
    end = False
    input_file_path = AbsolutePath.ensure(input_file_name)
    output_file_path = AbsolutePath.ensure(output_file_name)
    assert input_file_path.isfile()
    if output_file_path.exists():
        output_file_path.delete()

    process = await asyncio.subprocess.create_subprocess_exec('runVideoRaptorBatch',
                                                              input_file_name,
                                                              output_file_name,
                                                              stdout=asyncio.subprocess.PIPE,
                                                              stderr=asyncio.subprocess.PIPE)
    while True:
        line = (await process.stdout.readline()).decode().strip()
        if not line and process.stdout.at_eof():
            break
        if line:
            if line.startswith('#'):
                if line.startswith('#count '):
                    nb_read = int(line[7:])
                elif line.startswith('#loaded '):
                    nb_loaded = int(line[8:])
                elif line == '#end':
                    end = True
            else:
                step = int(line)
                notifier.notify(notifications.VideoJob(job_id, step, job_count))
    program_errors = (await process.stderr.read()).decode().strip()
    if not end and program_errors:
        raise Exception('Video-to-JSON error: ' + program_errors)
    assert nb_read == job_count
    notifier.notify(notifications.VideoJob(job_id, job_count, job_count))
    return nb_loaded


async def job_video_thumbnails_to_json(job):
    input_file_name, output_file_name, job_count, job_id, notifier = job

    nb_read = 0
    nb_loaded = 0
    end = False
    input_file_path = AbsolutePath.ensure(input_file_name)
    output_file_path = AbsolutePath.ensure(output_file_name)
    assert input_file_path.isfile()
    if output_file_path.exists():
        output_file_path.delete()

    process = await asyncio.subprocess.create_subprocess_exec('runVideoRaptorThumbnails',
                                                              input_file_name,
                                                              output_file_name,
                                                              stdout=asyncio.subprocess.PIPE,
                                                              stderr=asyncio.subprocess.PIPE)
    while True:
        line = (await process.stdout.readline()).decode().strip()
        if not line and process.stdout.at_eof():
            break
        if line:
            if line.startswith('#'):
                if line.startswith('#count '):
                    nb_read = int(line[7:])
                elif line.startswith('#loaded '):
                    nb_loaded = int(line[8:])
                elif line == '#end':
                    end = True
            else:
                step = int(line)
                notifier.notify(notifications.ThumbnailJob(job_id, step, job_count))
    program_errors = (await process.stderr.read()).decode().strip()
    if not end and program_errors:
        raise Exception('Videos-thumbnails-to-JSON error: ' + program_errors)
    assert nb_read == job_count
    notifier.notify(notifications.ThumbnailJob(job_id, job_count, job_count))
    return nb_loaded


def asynchronous_batch(function, jobs):
    async def f():
        return await asyncio.gather(*[function(job) for job in jobs])

    return asyncio.run(f())
