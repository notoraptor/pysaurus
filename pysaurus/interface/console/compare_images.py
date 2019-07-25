import concurrent.futures
import os
import sys
from typing import Any, List, Tuple

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.profiling import Profiler
from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.utils.functions import dispatch_tasks, timestamp_microseconds
from pysaurus.core.video_raptor import alignment as native_alignment
from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.public.api import API
from pysaurus.wip.image_utils import DEFAULT_THUMBNAIL_SIZE

PRINT_STEP = 500
SIM_LIMIT = 0.9
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
        miniatures.append(Miniature.from_file_name(thumbnail_path.path, DEFAULT_THUMBNAIL_SIZE, file_name))
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


def find_similar_images_3(miniatures):
    # type: (List[Miniature]) -> List[List[Tuple[int, float]]]
    results = native_alignment.classify_similarities(miniatures, SIM_LIMIT, 255)
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
    list_file_path = sys.argv[1] if len(sys.argv) > 1 else None
    database = API.load_database(list_file_path=list_file_path)
    miniatures = generate_miniatures(database)
    print('Extracted miniatures from %d/%d videos.' % (len(miniatures), database.nb_valid))

    sim_groups = find_similar_images_3(miniatures)
    print('Finally found', len(sim_groups), 'similarity groups.')

    html_dir = AbsolutePath('.html')
    unique_id = timestamp_microseconds()
    if sim_groups:
        if html_dir.isdir():
            for file_name in html_dir.listdir():
                if file_name.endswith('.html'):
                    AbsolutePath.join(html_dir, file_name).delete()
        elif html_dir.isfile():
            raise OSError('Path .html is a file, not a directory.')
        else:
            os.makedirs(html_dir.path, exist_ok=True)

    for i, g in enumerate(sim_groups):
        similar_group_to_html_file(i + 1, g, miniatures, database, html_dir, unique_id)
    print(sum(len(g) for g in sim_groups), 'similar images from', len(miniatures), 'total images.')


if __name__ == '__main__':
    main()
