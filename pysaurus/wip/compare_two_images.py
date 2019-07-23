import os
import sys

import math
from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.wip import image_utils
from pysaurus.wip.find_similar_images import is_image
from pysaurus.wip.moderator_function import super_generator, ultimate_generator
from pysaurus.wip.pillow_wip import MAX_PIXEL_DISTANCE

V = MAX_PIXEL_DISTANCE
H = MAX_PIXEL_DISTANCE / 2
P = MAX_PIXEL_DISTANCE / 4
B = V / 2

super_moderate = super_generator(V, B)

SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
simple_super_moderate = super_generator(SIMPLE_MAX_PIXEL_DISTANCE, SIMPLE_MAX_PIXEL_DISTANCE / 2)


def similar_group_to_html_file(group_id, group, html_dir):
    size = len(group)
    html = StringPrinter()
    html.write('<html>')
    html.write('<header>')
    html.write('<meta charset="utf-8"/>')
    html.write('<title>Thumbnails similarities for group %s</title>' % group_id)
    html.write('<link rel="stylesheet" href="similarities.css"/>')
    html.write('</header>')
    html.write('<body>')
    html.write('<h1>%d files</h1>' % size)
    html.write('<table>')
    html.write('<thead>')
    html.write('<tr><th class="group-id">Group ID</th><th class="thumbnails">Thumbnails</th></tr>')
    html.write('<tbody>')
    html.write('<tr>')
    html.write('<td class="group-id">%s</td>' % group_id)
    html.write('<td class="thumbnails">')
    for thumb_path, score in group:
        html.write('<div class="thumbnail">')
        html.write('<div class="image">')
        html.write('<img src="file://%s"/>' % thumb_path)
        html.write('</div>')
        html.write('<div><strong>%s</strong></div>' % score)
        html.write('<div><code>%s</code></div>' % thumb_path)
        html.write('</div>')
    html.write('</td>')
    html.write('</tr>')
    html.write('</tbody>')
    html.write('</thead>')
    html.write('</table>')
    html.write('</body>')
    html.write('</html>')

    output_file_name = AbsolutePath.join(html_dir, 'sim.%s.html' % (group_id))
    os.makedirs(html_dir, exist_ok=True)
    with open(output_file_name.path, 'w') as file:
        file.write(str(html))


def pixel_similarity(p1, p2):
    dr = p1.r - p2.r
    dg = p1.g - p2.g
    db = p1.b - p2.b
    d = math.sqrt(dr * dr + dg * dg + db * db)
    return (MAX_PIXEL_DISTANCE - super_moderate(d)) / MAX_PIXEL_DISTANCE


def pixel_raw_sim(p1, p2):
    d = abs(p1.r - p2.r) + abs(p1.g - p2.g) + abs(p1.b - p2.b)
    return (SIMPLE_MAX_PIXEL_DISTANCE - simple_super_moderate(d)) / SIMPLE_MAX_PIXEL_DISTANCE


def compare(miniature_1, miniature_2, radius=1):
    # type: (Miniature, Miniature, int) -> float
    score = 0
    for x in range(miniature_1.width):
        for y in range(miniature_1.height):
            pixel_1 = miniature_1.pixel_at(x, y)
            pixels_around = [miniature_2.pixel_at(other_x, other_y)
                             for (other_x, other_y) in miniature_1.coordinates_around(x, y, radius=radius)]
            score += max(pixel_raw_sim(pixel_1, other_pixel) for other_pixel in pixels_around)
    return score / (miniature_1.width * miniature_1.height)


def find(user_path):
    score_limit = 0.9
    thumbnail_size = image_utils.DEFAULT_THUMBNAIL_SIZE
    miniatures = []
    print('Collecting miniatures.')
    for path in os.listdir(user_path):
        if is_image(path):
            img = os.path.join(user_path, path)
            miniatures.append(Miniature.from_file_name(img, dimensions=thumbnail_size, identifier=img))
            if len(miniatures) % 100 == 0:
                print('Collected', len(miniatures), 'miniatures.')
    print('Finished collecting', len(miniatures), 'miniatures.')
    print('Comparing miniatures.')
    classes = [(i, 1.) for i in range(len(miniatures))]
    for i in range(len(miniatures)):
        for j in range(i + 1, len(miniatures)):
            score = compare(miniatures[i], miniatures[j])
            if score >= score_limit:
                classes[j] = (classes[i][0], score)
        if i % 100 == 0:
            print('Comparing miniature', i + 1, '/', len(miniatures))
    print('Finished comparing', len(miniatures), 'miniatures.')
    groups = {}
    for index_image, (image_class, image_score) in enumerate(classes):
        groups.setdefault(image_class, []).append((miniatures[index_image].identifier, image_score))
    valid_groups = [group for group in groups.values() if len(group) > 1]
    if valid_groups:
        print('Found', len(valid_groups), 'similar images.')
        for i, group in enumerate(valid_groups):
            similar_group_to_html_file(i, group, '.similar')


def main():
    if len(sys.argv) < 3:
        return
    print(simple_super_moderate.__name__)
    thumbnail_size = image_utils.DEFAULT_THUMBNAIL_SIZE
    miniature_1 = Miniature.from_file_name(sys.argv[1], dimensions=thumbnail_size)
    miniature_2 = Miniature.from_file_name(sys.argv[2], dimensions=thumbnail_size)
    radius = int(sys.argv[3]) if len(sys.argv) == 4 else 1
    print(compare(miniature_1, miniature_2, radius))


def main2():
    if len(sys.argv) != 2:
        return
    find(sys.argv[1])


if __name__ == '__main__':
    main()
