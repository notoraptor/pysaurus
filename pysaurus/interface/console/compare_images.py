import concurrent.futures
import os
from typing import List, Tuple

from pysaurus.core.database.database import Database
from pysaurus.core.profiling import Profiler
from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.utils.functions import dispatch_tasks, timestamp_microseconds
from pysaurus.public.api import API
from pysaurus.wip.image_utils import ImageComparator
from pysaurus.core.video_raptor.api import ThumbnailChannels
from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.video_raptor import api as video_raptor

PRINT_STEP = 500


def job_generate_gray_arrays(job):
    # type: (Tuple[list, str, ImageComparator]) -> List[ThumbnailChannels]
    thumbnails, job_id, comparator = job
    nb_videos = len(thumbnails)
    gray_arrays = []
    count = 0
    for file_name, thumbnail_path in thumbnails:
        if thumbnail_path.isfile():
            gray_arrays.append(comparator.to_thumbnail_channels(thumbnail_path.path, file_name))
        count += 1
        if count % PRINT_STEP == 0:
            print('[JOB %s] %d/%d' % (job_id, count, nb_videos))
    print('[JOB %s] %d/%d' % (job_id, count, nb_videos))
    return gray_arrays


def job_resolve_sim_group(job):
    potential_sim_group, comparator, sim_limit, diff_limit = job

    alone_indices = []
    sim_groups = []
    new_potential_sim_groups = []

    index_ref_thumb, ref_channels = potential_sim_group[0]
    ref_sim_group = [(index_ref_thumb, 1)]
    ref_diff_group = []
    for index_group in range(1, len(potential_sim_group)):
        index_local_thumb, local_channels = potential_sim_group[index_group]
        score = comparator.align_channels_by_diff(ref_channels, local_channels)
        if score >= sim_limit:
            ref_sim_group.append((index_local_thumb, score))
        else:
            ref_diff_group.append((index_local_thumb, score))

    if len(ref_sim_group) == 1:
        alone_indices.append(ref_sim_group[0][0])
    else:
        print('Found', len(ref_sim_group), 'similar images.')
        sim_groups.append(ref_sim_group)

    ref_diff_group.sort(key=lambda couple: couple[1])
    nb_ref_diff_group = len(ref_diff_group)
    start = 0
    cursor = 1
    while cursor < nb_ref_diff_group:
        groups = []
        start_score = ref_diff_group[start][1]
        curr_score = ref_diff_group[cursor][1]
        if abs(start_score - curr_score) > diff_limit:
            groups.append([ref_diff_group[i][0] for i in range(start, cursor)])
            if cursor == nb_ref_diff_group - 1:
                alone_indices.append(ref_diff_group[cursor][0])
            else:
                start = cursor
        elif cursor == nb_ref_diff_group - 1:
            groups.append([ref_diff_group[i][0] for i in range(start, nb_ref_diff_group)])
        for group in groups:
            if len(group) == 1:
                alone_indices.append(group[0])
            else:
                new_potential_sim_groups.append(group)
        cursor += 1

    return sim_groups, new_potential_sim_groups, alone_indices


def generate_thumbnails_channels(database, comparator):
    # type: (Database, ImageComparator) -> List[ThumbnailChannels]
    thumbnails_channels = []
    cpu_count = os.cpu_count()
    tasks = [(video.filename, video.get_thumbnail_path(database.folder))
             for video in database.valid_videos_with_thumbnails]
    jobs = dispatch_tasks(tasks, cpu_count, [comparator])
    with Profiler('Generating gray arrays.'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(job_generate_gray_arrays, jobs))
    for local_array in results:
        thumbnails_channels.extend(local_array)
    return thumbnails_channels

def classify_similarities(job):
    return video_raptor.classify_similarities(*job)

def find_similar_images(thumbnails_channels, comparator):
    # type: (List[ThumbnailChannels], ImageComparator) -> List[List[Tuple[int, float]]]
    sim_limit = 0.94
    diff_limit = 1 - sim_limit
    sim_groups = []
    alone_indices = []
    cpu_count = os.cpu_count() - 1

    with Profiler('Looking for similar images.'):
        potential_sim_groups = [list(range(len(thumbnails_channels)))]
        while potential_sim_groups:
            print('Checking', sum(len(g) for g in potential_sim_groups), 'images in',
                  len(potential_sim_groups), 'groups.')

            jobs = [(g,
                     [thumbnails_channels[i] for i in g],
                     comparator.width,
                     comparator.height,
                     comparator.min_val,
                     comparator.max_val,
                     comparator.aligner.gap_score,
                     sim_limit,
                     diff_limit)
                    for g in potential_sim_groups]

            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = executor.map(classify_similarities, jobs)

            new_potential_sim_groups = []
            for (local_sim_groups, local_new_potential_sim_groups, local_alone_indices) in results:
                sim_groups.extend(local_sim_groups)
                new_potential_sim_groups.extend(local_new_potential_sim_groups)
                alone_indices.extend(local_alone_indices)
                if local_sim_groups and len(local_sim_groups[0]) > 1:
                    print('Found', len(local_sim_groups[0]), 'similar images.')

            potential_sim_groups = new_potential_sim_groups

    return sim_groups


def similar_group_to_html_file(group_id, group, gray_arrays, database, html_dir, unique_id):
    # type: (int, List[Tuple[int, float]], List[ThumbnailChannels], Database, AbsolutePath, object) -> None
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
        thumb_channels = gray_arrays[image_index]
        thumb_path = database.get_video_from_filename(thumb_channels.identifier).get_thumbnail_path(database.folder)
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


def main():
    database = API.load_database()
    comparator = ImageComparator()
    thumbnails_channels = generate_thumbnails_channels(database, comparator)
    print('Extracted thumbnails channels from %d/%d videos.' % (len(thumbnails_channels), database.nb_valid))

    sim_groups = find_similar_images(thumbnails_channels, comparator)

    print()
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

    for i, g in enumerate(sorted(sim_groups, key=lambda v: len(v))):
        similar_group_to_html_file(i + 1, g, thumbnails_channels, database, html_dir, unique_id)
    print(sum(len(g) for g in sim_groups), 'similar images from', len(thumbnails_channels), 'total images.')


if __name__ == '__main__':
    main()
