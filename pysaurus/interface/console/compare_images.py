import concurrent.futures
import os

from pysaurus.core.profiling import Profiler
from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.utils.functions import dispatch_tasks
from pysaurus.public.api import API
from pysaurus.wip.image_utils import ImageComparator
from pysaurus.core.components.absolute_path import AbsolutePath
from typing import List, Tuple

BATCH_SIZE = 500


class GrayThumbnail:
    __slots__ = ('array', 'file_path', 'thumbnail_path')

    def __init__(self, array, file_path, thumbnail_path):
        # type: (List[List[int]], AbsolutePath, AbsolutePath) -> None
        self.array = array
        self.file_path = file_path
        self.thumbnail_path = thumbnail_path


def job_generate_gray_arrays(job):
    thumbnails, job_id, comparator = job
    nb_videos = len(thumbnails)
    gray_arrays = []
    count = 0
    for file_name, thumbnail_path in thumbnails:
        if thumbnail_path.isfile():
            gray_arrays.append(GrayThumbnail(
                array=comparator.to_thumbnail_gray_array(thumbnail_path.path),
                file_path=file_name,
                thumbnail_path=thumbnail_path
            ))
        count += 1
        if count % BATCH_SIZE == 0:
            print('[JOB %s] %d/%d' % (job_id, count, nb_videos))
    print('[JOB %s] %d/%d' % (job_id, count, nb_videos))
    return gray_arrays


def similar_group_to_html_file(group_id, group, gray_arrays):
    # type: (int, List[Tuple[int, float]], List[GrayThumbnail]) -> None
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
        thumb_path = gray_arrays[image_index].thumbnail_path
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
    os.makedirs('.html', exist_ok=True)
    with open('.html/sim.%03d.html' % group_id, 'w') as file:
        file.write(str(html))


def main():
    database = API.load_database()
    comparator = ImageComparator()
    gray_arrays = []  # type: List[GrayThumbnail]
    cpu_count = os.cpu_count()
    tasks = [(video.filename, video.get_thumbnail_path(database.folder)) for video in database.valid_videos]
    jobs = dispatch_tasks(tasks, cpu_count, [comparator])
    with Profiler('Generating gray arrays.'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(job_generate_gray_arrays, jobs))
    for local_array in results:
        gray_arrays.extend(local_array)
    nb_gray_arrays = len(gray_arrays)
    print('Generated gray arrays for %d/%d videos.' % (nb_gray_arrays, len(tasks)))

    sim_limit = 0.94
    diff_limit = 0.1
    sim_groups = []
    potential_alone_arrays = []

    with Profiler('Looking for similar images.'):
        potential_sim_groups = [list(range(nb_gray_arrays))]
        while potential_sim_groups:
            print(len(potential_sim_groups), 'groups to check')
            new_potential_sim_groups = []
            for potential_sim_group in potential_sim_groups:
                ref_index = potential_sim_group[0]
                ref_sim_group = [(ref_index, 1)]
                ref_diff_group = []
                ref_array = gray_arrays[ref_index].array
                for j in range(1, len(potential_sim_group)):
                    i = potential_sim_group[j]
                    score = comparator.align_by_diff(ref_array, gray_arrays[i].array)
                    if score >= sim_limit:
                        ref_sim_group.append((i, score))
                    else:
                        ref_diff_group.append((i, score))

                if len(ref_sim_group) == 1:
                    potential_alone_arrays.append(ref_sim_group[0][0])
                else:
                    print('Found', len(ref_sim_group), 'potential similar images.')
                    sim_groups.append(ref_sim_group)

                ref_diff_group.sort(key=lambda couple: couple[1])
                nb_ref_diff_group = len(ref_diff_group)
                start = 0
                cursor = 1
                while cursor < nb_ref_diff_group:
                    start_score = ref_diff_group[start][1]
                    curr_score = ref_diff_group[cursor][1]
                    groups = []
                    if abs(start_score - curr_score) >= diff_limit:
                        groups.append([index for index, _ in ref_diff_group[start:cursor]])
                        if cursor == nb_ref_diff_group - 1:
                            groups.append([ref_diff_group[cursor][0]])
                        else:
                            start = cursor
                    elif cursor == nb_ref_diff_group - 1:
                        groups.append([index for index, _ in ref_diff_group[start:]])
                    for group in groups:
                        if len(group) == 1:
                            potential_alone_arrays.append(group[0])
                        else:
                            new_potential_sim_groups.append(group)
                    cursor += 1
            potential_sim_groups = new_potential_sim_groups

    print()
    print('Finally found', len(sim_groups), 'similarity groups.')
    total = 0
    for i, g in enumerate(sorted(sim_groups, key=lambda v: len(v))):
        total += len(g)
        similar_group_to_html_file(i + 1, g, gray_arrays)
    print(total, 'similar images from', nb_gray_arrays, 'total images.')


if __name__ == '__main__':
    main()
