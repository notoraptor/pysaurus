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

SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
moderate = super_generator(SIMPLE_MAX_PIXEL_DISTANCE, SIMPLE_MAX_PIXEL_DISTANCE / 2)


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
    d = abs(p1.r - p2.r) + abs(p1.g - p2.g) + abs(p1.b - p2.b)
    return (SIMPLE_MAX_PIXEL_DISTANCE - moderate(d)) / SIMPLE_MAX_PIXEL_DISTANCE


def pixel_distance(p1, p2):
    return moderate(abs(p1.r - p2.r) + abs(p1.g - p2.g) + abs(p1.b - p2.b))


def compare(miniature_1, miniature_2, radius=1):
    # type: (Miniature, Miniature, int) -> float
    size = miniature_1.width * miniature_1.height
    distance = 0
    for x in range(miniature_1.width):
        for y in range(miniature_1.height):
            pixel_1 = miniature_1.pixel_at(x, y)
            pixels_around = [miniature_2.pixel_at(other_x, other_y)
                             for (other_x, other_y) in miniature_1.coordinates_around(x, y, radius=radius)]
            distance += min(pixel_distance(pixel_1, other_pixel) for other_pixel in pixels_around)
    return (SIMPLE_MAX_PIXEL_DISTANCE * size - distance) / (SIMPLE_MAX_PIXEL_DISTANCE * size)


def main():
    if len(sys.argv) < 3:
        return
    print('Moderator:', moderate.__name__)
    thumbnail_size = image_utils.DEFAULT_THUMBNAIL_SIZE
    miniature_1 = Miniature.from_file_name(sys.argv[1], dimensions=thumbnail_size)
    miniature_2 = Miniature.from_file_name(sys.argv[2], dimensions=thumbnail_size)
    histogram_1 = miniature_1.to_histogram()
    histogram_2 = miniature_2.to_histogram()
    print('Histogram 1:', histogram_1.nb_colors, 'colors for', histogram_1.nb_pixels, 'pixels')
    print('Histogram 2:', histogram_2.nb_colors, 'colors for', histogram_2.nb_pixels, 'pixels')
    radius = int(sys.argv[3]) if len(sys.argv) == 4 else 1
    print('Score:', compare(miniature_1, miniature_2, radius))


if __name__ == '__main__':
    main()
