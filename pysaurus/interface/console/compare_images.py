import concurrent.futures
import os
from typing import Any, List, Tuple
import math

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.profiling import Profiler
from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.utils.functions import dispatch_tasks, timestamp_microseconds
from pysaurus.core.video_raptor import alignment as native_alignment
from pysaurus.core.video_raptor.alignment_utils import IntensityPoint, IntensitySequence, Miniature
from pysaurus.public.api import API
from pysaurus.wip.image_utils import ImageComparator, save_gray_image

PRINT_STEP = 500
SIM_LIMIT = 0.94


def job_generate_miniatures(job):
    # type: (Tuple[list, str, ImageComparator]) -> List[Miniature]
    thumbnails, job_id, comparator = job
    nb_videos = len(thumbnails)
    miniatures = []
    count = 0
    for file_name, thumbnail_path in thumbnails:
        if thumbnail_path.isfile():
            miniatures.append(comparator.to_miniature(thumbnail_path.path, file_name))
        count += 1
        if count % PRINT_STEP == 0:
            print('[JOB %s] %d/%d' % (job_id, count, nb_videos))
    print('[JOB %s] %d/%d' % (job_id, count, nb_videos))
    return miniatures


def generate_miniatures(database, comparator):
    # type: (Database, ImageComparator) -> List[Miniature]
    miniatures = []  # type: List[Miniature]
    cpu_count = os.cpu_count()
    tasks = [(video.filename, video.get_thumbnail_path(database.folder))
             for video in database.valid_videos_with_thumbnails]
    jobs = dispatch_tasks(tasks, cpu_count, [comparator])
    with Profiler('Generating miniatures.'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(job_generate_miniatures, jobs))
    for local_array in results:
        miniatures.extend(local_array)
    return miniatures


def split_vs_intensity_points(indices, miniatures, diff_limit):
    # type: (List[int], List[Miniature], float) -> List[List[int]]
    nb_indices = len(indices)
    miniature_0 = miniatures[indices[0]]
    aligner = IntensitySequence(miniature_0.width, miniature_0.height)
    ipc = []
    for index in indices:
        ggi = miniatures[index].to_intensity_points()
        score = aligner.align_points([], ggi)
        ipc.append((index, score))
    ipc.sort(key=lambda couple: couple[1])
    nb_ipc = len(ipc)
    ipc_groups = []
    start = 0
    cursor = start + 1
    while cursor < nb_ipc:
        distance = ipc[start][1] - ipc[cursor][1]
        if distance < -diff_limit or distance > diff_limit:
            ipc_groups.append([ipc[i][0] for i in range(start, cursor)])
            start = cursor
        cursor += 1
    ipc_groups.append([ipc[i][0] for i in range(start, nb_ipc)])
    return ipc_groups


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


def draw_rectangles(miniatures):
    # type: (List[Miniature]) -> None
    sequences = [miniature.to_intensity_points() for miniature in miniatures]
    rectangles = [IntensitySequence.get_rectangle(sequence) for sequence in sequences]
    width = miniatures[0].width
    height = miniatures[0].height
    factor = 200
    output_width = width * factor
    output_height = height * factor
    output = [([255] * output_width) for _ in range(output_height)]
    for i, rectangle in enumerate(rectangles):
        y_min = int(rectangle.top * factor)
        x_min = int(rectangle.left * factor)
        y_max = int(rectangle.bottom * factor)
        x_max = int(rectangle.right * factor)
        print(i + 1, '/', len(rectangles), ((x_min, y_min), (x_max, y_max)))
        value = 200 if i % 2 == 0 else 0
        for x in range(x_min, x_max + 1):
            for y in (y_min, y_max):
                output[y][x] = value
        for y in range(y_min, y_max + 1):
            for x in (x_min, x_max):
                output[y][x] = value
    data = []
    for line in output:
        data.extend(line)
    save_gray_image(output_width, output_height, data, 'rectangles.png')
    exit(0)


def draw_lines(miniatures):
    # type: (List[Miniature]) -> None
    sequences = [miniature.to_intensity_points() for miniature in miniatures]
    width = miniatures[0].width
    height = miniatures[0].height
    factor = 200
    output_width = width * factor
    output_height = height * factor
    output = [([255] * output_width) for _ in range(output_height)]
    for i, sequence in enumerate(sequences):
        if i % 500 == 0:
            print(i + 1)
        value = 200 if i % 2 == 0 else 0
        len_sequence = len(sequence)
        if len_sequence == 1:
            x = int(sequence[0].x * factor)
            y = int(sequence[0].y * factor)
            points = (
                (x - 1, y - 1),
                (x, y - 1),
                (x + 1, y - 1),
                (x - 1, y),
                (x, y),
                (x + 1, y),
                (x - 1, y + 1),
                (x, y + 1),
                (x + 1, y + 1),
            )
            for (h, v) in points:
                if 0 <= h < output_width and 0 <= v < output_height:
                    output[v][h] = value
            continue
        for i in range(len_sequence):
            x1 = sequence[i].x * factor
            y1 = sequence[i].y * factor
            x2 = sequence[(i + 1) % len_sequence].x * factor
            y2 = sequence[(i + 1) % len_sequence].y * factor
            if x1 == x2:
                x = int(x1)
                y_min = min(y1, y2)
                y_max = max(y1, y2)
                for y in range(int(y_min), int(y_max) + 1):
                    output[y][x] = value
                continue
            x_min = min(x1, x2)
            x_max = max(x1, x2)
            if y1 == y2:
                y = int(y1)
                for x in range(int(x_min), int(x_max) + 1):
                    output[y][x] = value
                continue
            a = (y1 - y2) / (x1 - x2)
            b = y1 - a * x1
            for x in range(int(x_min), int(x_max) + 1):
                y = int(a * x + b)
                if 0 <= y < output_height:
                    output[y][x] = value
    data = []
    for line in output:
        data.extend(line)
    save_gray_image(output_width, output_height, data, 'lines.png')
    exit(0)

def find_similar_images(miniatures, comparator):
    # type: (List[Miniature], ImageComparator) -> List[List[Tuple[int, float]]]
    sim_limit = SIM_LIMIT
    diff_limit = 1 - sim_limit
    sim_groups = []
    alone_indices = []
    cpu_count = os.cpu_count() - 1

    all_indices = list(range(len(miniatures)))

    # draw_rectangles(miniatures)
    draw_lines(miniatures)

    print('Computing potential similar groups based on intensity points comparison.')
    ip_results = split_vs_intensity_points(all_indices, miniatures, diff_limit)
    print('Splitting', sum(len(g) for g in ip_results), 'images in', len(ip_results), 'groups based on IP.')

    print('Computing potential similar groups based on comparison against white image.')
    wi_results = split_vs_white_image(all_indices, miniatures, comparator.aligner.gap_score, diff_limit)
    print('Splitting', sum(len(g) for g in wi_results), 'images in', len(wi_results), 'groups based on white image.')
    exit(0)

    with Profiler('Looking for similar images.'):
        potential_sim_groups = wi_results
        while potential_sim_groups:
            print('Checking', sum(len(g) for g in potential_sim_groups), 'images in',
                  len(potential_sim_groups), 'groups.')

            jobs = [(potential_sim_group,
                     [miniatures[i] for i in potential_sim_group],
                     comparator.width,
                     comparator.height,
                     comparator.min_val,
                     comparator.max_val,
                     comparator.aligner.gap_score,
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


def similar_group_to_html_file(group_id, group, miniatures, database, html_dir, unique_id, width, height):
    # type: (int, List[Tuple[int, float]], List[Miniature], Database, AbsolutePath, Any, int, int, int) -> None
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
    low = False
    size = width * height
    max_distance = math.sqrt((width - 1) ** 2 + (height - 1) ** 2)
    miniature_0 = miniatures[group[0][0]]
    aligner = IntensitySequence(width, height)
    for image_index, image_score in group:
        miniature_i = miniatures[image_index]
        gg0 = miniature_0.to_intensity_points()
        ggi = miniature_i.to_intensity_points()
        ts = aligner.align_points(gg0, ggi)
        thumb_path = database.get_video_from_filename(miniature_i.identifier).get_thumbnail_path(database.folder)
        html.write('<div class="thumbnail">')
        html.write('<div class="image">')
        html.write('<img src="file://%s"/>' % thumb_path)
        html.write('</div>')
        html.write('<div class="score">%s</div>' % image_score)
        html.write('<div class="score">gray: %s</div>' % ts)
        for g in ggi:
            html.write('<div><code>%s</code></div>' % g)
        low = low or ts < SIM_LIMIT
        html.write('</div>')
    html.write('</td>')
    html.write('</tr>')
    html.write('</tbody>')
    html.write('</thead>')
    html.write('</table>')
    html.write('</body>')
    html.write('</html>')

    output_file_name = AbsolutePath.join(html_dir, 'sim%s.%s.%03d.html' % ('.low' if low else '', unique_id, group_id))
    with open(output_file_name.path, 'w') as file:
        file.write(str(html))


def main():
    database = API.load_database()
    comparator = ImageComparator()
    thumbnails_channels = generate_miniatures(database, comparator)
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
        similar_group_to_html_file(i + 1, g, thumbnails_channels, database, html_dir, unique_id,
                                   comparator.width, comparator.height, comparator.aligner.gap_score)
    print(sum(len(g) for g in sim_groups), 'similar images from', len(thumbnails_channels), 'total images.')


if __name__ == '__main__':
    main()
