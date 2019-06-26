import concurrent.futures
import os

from pysaurus.core.profiling import Profiler
from pysaurus.core.utils.functions import dispatch_tasks
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


def main():
    database = API.load_database()
    comparator = ImageComparator()
    gray_arrays = []
    similarities = {}
    cpu_count = os.cpu_count()
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
    count = 0
    nb_comparisons = (nb_generated * (nb_generated - 1) // 2)
    with Profiler('Computing %d similarities.' % nb_comparisons):
        for i in range(nb_generated):
            file_name_1, array_1 = gray_arrays[i]
            local = {}
            for j in range(i + 1, nb_generated):
                file_name_2, array_2 = gray_arrays[j]
                score = comparator.align(array_1, array_2)
                local[file_name_2] = score
                if score > 0.5:
                    nb_strong_scores += 1
                count += 1
                if count % BATCH_SIZE == 0:
                    print('%d/%d' % (count, nb_comparisons))
            similarities[file_name_1] = local
    print('%d/%d' % (count, nb_comparisons))
    print('Found %d strong score(s).' % nb_strong_scores)

if __name__ == '__main__':
    main()
