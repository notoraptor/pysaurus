import concurrent.futures
import os
import time

from pysaurus.core.profiling import Profiler
from pysaurus.core.utils.functions import dispatch_tasks, count_couples, dispatch_combinations
from pysaurus.public.api import API
from pysaurus.wip.image_utils import ImageComparator

BATCH_SIZE = 500


def job_generate_gray_arrays(job):
    videos, job_id, folder, comparator = job
    nb_videos = len(videos)
    gray_arrays = []
    count = 0
    for video in videos:
        thumbnail_path = video.get_thumbnail_path(folder)
        if thumbnail_path.isfile():
            gray_arrays.append((video.filename, comparator.to_thumbnail_gray_array(thumbnail_path.path)))
        count += 1
        if count % BATCH_SIZE == 0:
            print('[JOB %s] %d/%d' % (job_id, count, nb_videos))
    print('[JOB %s] %d/%d' % (job_id, count, nb_videos))
    return gray_arrays


def job_align(job):
    intervals, job_id, gray_arrays, comparator = job
    total = 0
    count = 0
    for (i, a, b) in intervals:
        total += b - a + 1
    output = {}
    for (i, a, b) in intervals:
        file_name_1, array_1 = gray_arrays[i]
        local = {}
        for j in range(a, b + 1):
            file_name_2, array_2 = gray_arrays[j]
            local[file_name_2] = comparator.align(array_1, array_2)
            count += 1
            if count % BATCH_SIZE == 0:
                print('[JOB %s] %d/%d, on %d vs %d' % (job_id, count, total, i, j))
            time.sleep(1e-6)
        output.setdefault(file_name_1, {}).update(local)
    print('[JOB %s] %d/%d' % (job_id, count, total))
    return output


def main():
    database = API.load_database()
    comparator = ImageComparator()
    gray_arrays = []
    similarities = {}
    cpu_count = os.cpu_count()
    assert cpu_count
    valid_videos = list(database.valid_videos)
    jobs = dispatch_tasks(valid_videos, cpu_count, [database.folder, comparator])
    with Profiler('Generating gray arrays.'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(job_generate_gray_arrays, jobs))
    for local_array in results:
        gray_arrays.extend(local_array)
    nb_generated = len(gray_arrays)
    print('Generated gray arrays for %d/%d videos.' % (nb_generated, len(valid_videos)))
    nb_strong_scores = 0
    nb_comparisons = count_couples(nb_generated)
    align_cpu_count = cpu_count
    jobs_align = dispatch_combinations(nb_generated, align_cpu_count, [gray_arrays, comparator])
    with Profiler('Computing %d similarities.' % nb_comparisons):
        with concurrent.futures.ProcessPoolExecutor(max_workers=align_cpu_count) as executor:
            results = list(executor.map(job_align, jobs_align))
        for result in results:
            for file_name_1, scores_dict in result.items():
                similarities.setdefault(file_name_1, {}).update(scores_dict)
    assert len(similarities) == nb_generated, (len(similarities), nb_generated)
    print('Found %d strong score(s).' % nb_strong_scores)


if __name__ == '__main__':
    main()
