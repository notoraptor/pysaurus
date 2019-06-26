import concurrent.futures
import os
import time

from pysaurus.core.profiling import Profiler
from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.utils.functions import dispatch_tasks
from pysaurus.public.api import API
from pysaurus.wip.image_utils import ImageComparator

BATCH_SIZE = 500


def job_generate_gray_arrays(job):
    thumbnails, job_id, folder, comparator = job
    nb_videos = len(thumbnails)
    gray_arrays = []
    count = 0
    for file_name, thumbnail_path in thumbnails:
        if thumbnail_path.isfile():
            gray_arrays.append((file_name, comparator.to_thumbnail_gray_array(thumbnail_path.path), thumbnail_path))
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
    cpu_count = os.cpu_count()
    thumbnails = [(video.filename, video.get_thumbnail_path(database.folder)) for video in database.valid_videos]
    jobs = dispatch_tasks(thumbnails, cpu_count, [database.folder, comparator])
    with Profiler('Generating gray arrays.'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(job_generate_gray_arrays, jobs))
    for local_array in results:
        gray_arrays.extend(local_array)
    nb_generated = len(gray_arrays)
    print('Generated gray arrays for %d/%d videos.' % (nb_generated, len(thumbnails)))

    sim_limit = 0.75
    diff_limit = 0.1
    sim_groups = []
    potential_alone_arrays = []

    with Profiler('Looking for similar images.'):
        potential_sim_groups = [list(range(len(gray_arrays)))]
        while potential_sim_groups:
            print(len(potential_sim_groups), 'groups to check')
            new_potential_sim_groups = []
            for potential_sim_group in potential_sim_groups:
                print('Checking a group with', len(potential_sim_group), 'image(s).')
                ref_index = potential_sim_group[0]
                ref_sim_group = [(ref_index, 1)]
                ref_diff_group = []
                ref_array = gray_arrays[ref_index][1]
                for j in range(1, len(potential_sim_group)):
                    i = potential_sim_group[j]
                    score = comparator.align(ref_array, gray_arrays[i][1])
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
    print('Finally found', len(sim_groups), 'similarities.')
    total = 0
    for i, g in enumerate(sim_groups):
        total += len(g)
        print('[%d]' % (i + 1), 'COUNT', len(g), 'MIN SCORE', min(v[1] for v in g[1:]), 'MAX SCORE',
              max(v[1] for v in g[1:]))
        html = StringPrinter()
        html.write('<html>')
        html.write('<header>')
        html.write('<meta charset="utf-8"/>')
        html.write('<title>Thumbnails similarities for group %03d</title>' % (i + 1))
        html.write('<link rel="stylesheet" href="similarities.css"/>')
        html.write('</header>')
        html.write('<body>')
        html.write('<table>')
        html.write('<thead>')
        html.write('<tr><th>Group ID</th><th>Thumbnails</th></tr>')
        html.write('<tbody>')
        html.write('<tr>')
        html.write('<td>%d</td>' % (i + 1))
        html.write('<td>')
        for image_index, image_score in g:
            thumb_path = gray_arrays[image_index][2]
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
        print(total, 'similarities in', nb_generated, 'images.')
        with open('sim.%03d.html' % (i + 1), 'w') as file:
            file.write(str(html))
    print('End')


if __name__ == '__main__':
    main()
