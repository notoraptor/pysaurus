import concurrent.futures
import os
from typing import Any, List, Tuple

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.profiling import Profiler
from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.utils.functions import dispatch_tasks, timestamp_microseconds
from pysaurus.core.video_raptor import alignment as native_alignment
from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.public.api import API
from pysaurus.wip.image_utils import DEFAULT_THUMBNAIL_SIZE, image_to_miniature

PRINT_STEP = 500
SIM_LIMIT = 0.7
MIN_VAL = 0
MAX_VAL = 255
GAP_SCORE = -1


def job_generate_miniatures(job):
    # type: (Tuple[list, str]) -> List[Miniature]
    thumbnails, job_id = job
    nb_videos = len(thumbnails)
    miniatures = []
    count = 0
    for file_name, thumbnail_path in thumbnails:
        miniatures.append(image_to_miniature(thumbnail_path.path, DEFAULT_THUMBNAIL_SIZE, file_name))
        count += 1
        if count % PRINT_STEP == 0:
            print('[Generating miniatures on thread %s] %d/%d' % (job_id, count, nb_videos))
    print('[Generated miniatures on thread %s] %d/%d' % (job_id, count, nb_videos))
    return miniatures


def generate_miniatures(database):
    # type: (Database) -> List[Miniature]
    miniatures = []  # type: List[Miniature]
    cpu_count = os.cpu_count()
    tasks = [(video.filename, video.get_thumbnail_path(database.folder))
             for video in database.valid_videos_with_thumbnails]
    jobs = dispatch_tasks(tasks, cpu_count)
    with Profiler('Generating miniatures.'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(job_generate_miniatures, jobs))
    for local_array in results:
        miniatures.extend(local_array)
    miniatures.sort(key=lambda m: m.identifier)
    return miniatures


def split_vs_white_image(indices, miniatures, gap_score, diff_limit):
    # type: (List[int], List[Miniature], int, float) -> List[List[int]]
    against_white = []
    size = miniatures[0].width * miniatures[0].height
    global_min_score = min(0, 255, gap_score) * size
    global_max_score = max(0, 255, gap_score) * size
    for index in indices:
        miniature = miniatures[index]
        score = (sum(miniature.r) + sum(miniature.g) + sum(miniature.b) - 3 * global_min_score) / (
                3 * (global_max_score - global_min_score))
        assert 0 <= score <= 1
        against_white.append((index, score))
    against_white.sort(key=lambda couple: couple[1])
    nb_sequences = len(against_white)
    initial_groups = []
    start = 0
    cursor = start + 1
    while cursor < nb_sequences:
        distance = against_white[start][1] - against_white[cursor][1]
        if distance < -diff_limit or distance > diff_limit:
            initial_groups.append([against_white[i][0] for i in range(start, cursor)])
            start = cursor
        cursor += 1
    initial_groups.append([against_white[i][0] for i in range(start, nb_sequences)])
    return initial_groups


def find_similar_images(miniatures):
    # type: (List[Miniature]) -> List[List[Tuple[int, float]]]
    sim_limit = SIM_LIMIT
    diff_limit = 1 - sim_limit
    sim_groups = []
    alone_indices = []
    cpu_count = os.cpu_count() - 1
    width = miniatures[0].width
    height = miniatures[0].height

    all_indices = list(range(len(miniatures)))

    print('Computing potential similar groups based on comparison against white image.')
    wi_results = split_vs_white_image(all_indices, miniatures, GAP_SCORE, diff_limit)
    print('Splitting', sum(len(g) for g in wi_results), 'images in', len(wi_results), 'groups based on white image.')
    exit(0)

    with Profiler('Looking for similar images.'):
        potential_sim_groups = wi_results
        while potential_sim_groups:
            print('Checking', sum(len(g) for g in potential_sim_groups), 'images in',
                  len(potential_sim_groups), 'groups.')

            jobs = [(potential_sim_group,
                     [miniatures[i] for i in potential_sim_group],
                     width,
                     height,
                     MIN_VAL,
                     MAX_VAL,
                     GAP_SCORE,
                     sim_limit,
                     diff_limit)
                    for potential_sim_group in potential_sim_groups]

            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = executor.map(native_alignment.classify_similarities, jobs)

            new_potential_sim_groups = []
            for (local_sim_groups, local_new_potential_sim_groups, local_alone_indices) in results:
                sim_groups.extend(local_sim_groups)
                new_potential_sim_groups.extend(local_new_potential_sim_groups)
                alone_indices.extend(local_alone_indices)
                if local_sim_groups and len(local_sim_groups[0]) > 1:
                    print('Found', len(local_sim_groups[0]), 'similar images.')

            potential_sim_groups = new_potential_sim_groups

    return sim_groups


def similar_group_to_html_file(group_id, group, miniatures, database, html_dir, unique_id):
    # type: (int, List[Tuple[int, float]], List[Miniature], Database, AbsolutePath, Any) -> None
    size = len(group)
    min_score = min(value[1] for value in group[1:])
    max_score = max(value[1] for value in group[1:])
    html = StringPrinter()
    html.write('<html>')
    html.write('<header>')
    html.write('<meta charset="utf-8"/>')
    html.write('<title>Thumbnails similarities for group %03d</title>' % group_id)
    html.write('<link rel="stylesheet" href="similarities.css"/>')
    html.write('</header>')
    html.write('<body>')
    html.write('<h1>%d files, min score %s, max score %s</h1>' % (size, min_score, max_score))
    html.write('<table>')
    html.write('<thead>')
    html.write('<tr><th class="group-id">Group ID</th><th class="thumbnails">Thumbnails</th></tr>')
    html.write('<tbody>')
    html.write('<tr>')
    html.write('<td class="group-id">%d</td>' % group_id)
    html.write('<td class="thumbnails">')
    for image_index, image_score in group:
        miniature_i = miniatures[image_index]
        thumb_path = database.get_video_from_filename(miniature_i.identifier).get_thumbnail_path(database.folder)
        html.write('<div class="thumbnail">')
        html.write('<div class="image">')
        html.write('<img src="file://%s"/>' % thumb_path)
        html.write('</div>')
        html.write('<div class="score">%s</div>' % image_score)
        html.write('</div>')
    html.write('</td>')
    html.write('</tr>')
    html.write('</tbody>')
    html.write('</thead>')
    html.write('</table>')
    html.write('</body>')
    html.write('</html>')

    output_file_name = AbsolutePath.join(html_dir, 'sim.%s.%03d.html' % (unique_id, group_id))
    with open(output_file_name.path, 'w') as file:
        file.write(str(html))


def array_distance(a, b):
    # type: (List[int], List[int]) -> int
    return sum(abs(a[i] - b[i]) for i in range(len(a)))


def compare_miniatures(i, j):
    # type: (Miniature, Miniature) -> float
    n = i.width * i.height
    v = 255
    return (3 * n * v - array_distance(i.r, j.r) - array_distance(i.g, j.g) - array_distance(i.b, j.b)) / (3 * n * v)


def find_similar_images_2(miniatures):
    # type: (List[Miniature]) -> List[List[Tuple[int, float]]]
    interrupted = False
    scores = [None] * len(miniatures)
    with Profiler('Finding similar images using simpler comparison.'):
        try:
            for i in range(len(miniatures)):
                # if i == 1: raise KeyboardInterrupt()
                if scores[i] is not None:
                    continue
                scores[i] = (i, 1)
                for j in range(i + 1, len(miniatures)):
                    if scores[j] is not None:
                        continue
                    score = compare_miniatures(miniatures[i], miniatures[j])
                    if score >= SIM_LIMIT:
                        scores[j] = (i, score)
                        print('(', score, ')')
                        print('\t', miniatures[i].identifier)
                        print('\t', miniatures[j].identifier)
                    if ((i + 1) * (j + 1)) % (10 * PRINT_STEP) == 0:
                        print('At', i + 1, 'vs', j + 1, 'on', len(miniatures), 'value(s).')
        except KeyboardInterrupt as exc:
            interrupted = exc
    if interrupted:
        print('Min score', min(info[1] for info in scores if info is not None))
        print('Max score', max(info[1] for info in scores if info is not None))
        raise interrupted
    groups = {}
    for i, score_info in enumerate(scores):
        if score_info is not None:
            group_id, score = score_info
            groups.setdefault(group_id, []).append((i, score))
    print('Min score', min(info[1] for info in scores if info is not None))
    print('Max score', max(info[1] for info in scores if info is not None))
    return [groups[group_id] for group_id in sorted(groups)]


def find_similar_images_3(miniatures):
    # type: (List[Miniature]) -> List[List[Tuple[int, float]]]
    with Profiler('Finding similar images using simpler NATIVE comparison.'):
        results = native_alignment.classify_similarities_2(miniatures, SIM_LIMIT, 255)
    groups = {}
    min_score = None
    max_score = None
    for i, group_id, score in results:
        min_score = score if min_score is None else min(min_score, score)
        max_score = score if max_score is None else max(max_score, score)
        if group_id != -1:
            groups.setdefault(group_id, []).append((i, score))
    print('Min score', min_score)
    print('Max score', max_score)
    return [group for group in sorted(groups.values(), key=lambda g: max(v[1] for v in g)) if len(group) > 1]


def main():
    database = API.load_database()
    miniatures = generate_miniatures(database)
    print('Extracted miniatures from %d/%d videos.' % (len(miniatures), database.nb_valid))

    sim_groups = find_similar_images_3(miniatures)
    print('Finally found', len(sim_groups), 'similarity groups.')

    html_dir = AbsolutePath('.html')
    if html_dir.isdir():
        for file_name in html_dir.listdir():
            if file_name.endswith('.html'):
                AbsolutePath.join(html_dir, file_name).delete()
    elif html_dir.isfile():
        raise OSError('Path .html is a file, not a directory.')
    else:
        os.makedirs(html_dir.path, exist_ok=True)
    unique_id = timestamp_microseconds()

    for i, g in enumerate(sim_groups):
        similar_group_to_html_file(i + 1, g, miniatures, database, html_dir, unique_id)
    print(sum(len(g) for g in sim_groups), 'similar images from', len(miniatures), 'total images.')


if __name__ == '__main__':
    main()
