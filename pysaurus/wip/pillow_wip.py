import math
import sys

from PIL import Image

from pysaurus.core.video_raptor import api as video_raptor
from pysaurus.wip.aligner import Aligner
from pysaurus.wip.image_utils import ImageComparator

R, G, B = 0, 1, 2
CHANNELS = (R, G, B)
BLACK = (0, 0, 0)
PIXEL_DISTANCE_TRESHOLD = 1


def get_segmentation(image, threshold):
    output = []
    previous_pixel = None
    for index_pixel, pixel in enumerate(image.getdata()):
        if index_pixel % image.width == 0:
            output.append(255)
        else:
            previous_red, previous_green, previous_blue = previous_pixel
            red, green, blue = pixel
            distance_red = abs(red - previous_red)
            distance_green = abs(green - previous_green)
            distance_blue = abs(blue - previous_blue)
            output.append(min(255 if dst < threshold else 0 for dst in (distance_red, distance_green, distance_blue)))
        previous_pixel = pixel
    return output


def flat_to_coord(index_pixel, width):
    # i => (x, y)
    return index_pixel % width, index_pixel // width


def coord_to_flat(x, y, width):
    # (x, y) => i
    return y * width + x


def refine_pixel(pixel, pixels_around):
    local_colors = {pixel: 1}
    for other_pixel in pixels_around:
        local_colors.setdefault(other_pixel, 0)
        local_colors[other_pixel] += 1
    max_colors = []
    max_count = None
    for color, count in local_colors.items():
        if max_count is None or max_count < count:
            max_count = count
            max_colors.clear()
            max_colors.append(color)
        elif max_count == count:
            max_colors.append(color)
    if pixel in max_colors:
        output_pixel = pixel
        nb_refined = 0
    elif len(max_colors) == 1:
        output_pixel = max_colors[0]
        nb_refined = 1
    else:
        output_pixel = sorted(max_colors)[0]
        nb_refined = 1
    return output_pixel, nb_refined


def positions_around(x, y, width, height):
    around = []
    if x - 1 >= 0:
        if y - 1 >= 0:
            around.append((x - 1, y - 1))
        if y + 1 < height:
            around.append((x - 1, y + 1))
        around.append((x - 1, y))
    if x + 1 < width:
        if y - 1 >= 0:
            around.append((x + 1, y - 1))
        if y + 1 < height:
            around.append((x + 1, y + 1))
        around.append((x + 1, y))
    if y - 1 >= 0:
        around.append((x, y - 1))
    if y + 1 < height:
        around.append((x, y + 1))
    return around


class Refinement:
    def __init__(self, width, height):
        self.output = []
        self.nb_refined = 0
        self.refined_coords = []
        self.width = width
        self.height = height

    def add(self, pixel, is_refined, x, y):
        self.output.append(pixel)
        self.nb_refined += is_refined
        if is_refined:
            self.refined_coords.append((x, y))

    def optimize(self):
        assert self.nb_refined == len(self.refined_coords)
        print('(0)', self.nb_refined)
        if not self.nb_refined:
            return
        refined_coords = self.refined_coords
        count_steps = 0
        while True:
            new_refined_pixels = []
            coords_to_check = set()
            for x, y in refined_coords:
                for other_x, other_y in positions_around(x, y, self.width, self.height):
                    coords_to_check.add((other_x, other_y))
            for x, y in coords_to_check:
                pixel, is_refined = refine_pixel(
                    self.output[coord_to_flat(x, y, self.width)],
                    [self.output[coord_to_flat(other_x, other_y, self.width)]
                     for (other_x, other_y) in positions_around(x, y, self.width, self.height)])
                if is_refined:
                    new_refined_pixels.append((x, y, pixel))
            count_steps += 1
            print('(%d)' % count_steps, len(new_refined_pixels),
                  '[%s]' % (['less', 'MORE'][len(new_refined_pixels) > len(refined_coords)]))
            if not new_refined_pixels:  # or len(new_refined_pixels) > len(refined_coords):
                print('END')
                break
            refined_coords.clear()
            for x, y, pixel in new_refined_pixels:
                refined_coords.append((x, y))
                self.output[coord_to_flat(x, y, self.width)] = pixel
            self.refined_coords = refined_coords
            self.nb_refined = len(refined_coords)


def refine(pixels_vector, width, height):
    refinement = Refinement(width, height)

    # Refine all pixels.
    refinement_top_left, top_left_is_refined = refine_pixel(
        pixels_vector[coord_to_flat(0, 0, width)],
        [pixels_vector[coord_to_flat(1, 0, width)],
         pixels_vector[coord_to_flat(1, 1, width)],
         pixels_vector[coord_to_flat(0, 1, width)]])
    refinement_top_right, top_right_is_refined = refine_pixel(
        pixels_vector[coord_to_flat(width - 1, 0, width)],
        [pixels_vector[coord_to_flat(width - 2, 0, width)],
         pixels_vector[coord_to_flat(width - 2, 1, width)],
         pixels_vector[coord_to_flat(width - 1, 1, width)]])
    refinement_bottom_left, bottom_left_is_refined = refine_pixel(
        pixels_vector[coord_to_flat(0, height - 1, width)],
        [pixels_vector[coord_to_flat(0, height - 2, width)],
         pixels_vector[coord_to_flat(1, height - 1, width)],
         pixels_vector[coord_to_flat(1, height - 2, width)]])
    refinement_bottom_right, bottom_right_is_refined = refine_pixel(
        pixels_vector[coord_to_flat(width - 1, height - 1, width)],
        [pixels_vector[coord_to_flat(width - 1, height - 2, width)],
         pixels_vector[coord_to_flat(width - 2, height - 2, width)],
         pixels_vector[coord_to_flat(width - 2, height - 1, width)]])
    refinements_top = [
        refine_pixel(
            pixels_vector[coord_to_flat(i, 0, width)],
            [pixels_vector[coord_to_flat(i - 1, 0, width)],
             pixels_vector[coord_to_flat(i - 1, 1, width)],
             pixels_vector[coord_to_flat(i, 1, width)],
             pixels_vector[coord_to_flat(i + 1, 1, width)],
             pixels_vector[coord_to_flat(i + 1, 0, width)]])
        for i in range(1, width - 1)]
    refinements_bottom = [
        refine_pixel(
            pixels_vector[coord_to_flat(i, height - 1, width)],
            [pixels_vector[coord_to_flat(i - 1, height - 1, width)],
             pixels_vector[coord_to_flat(i - 1, height - 2, width)],
             pixels_vector[coord_to_flat(i, height - 2, width)],
             pixels_vector[coord_to_flat(i + 1, height - 2, width)],
             pixels_vector[coord_to_flat(i + 1, height - 1, width)]])
        for i in range(1, width - 1)]
    refinements_left = [
        refine_pixel(
            pixels_vector[coord_to_flat(0, j, width)],
            [pixels_vector[coord_to_flat(0, j - 1, width)],
             pixels_vector[coord_to_flat(1, j - 1, width)],
             pixels_vector[coord_to_flat(1, j, width)],
             pixels_vector[coord_to_flat(1, j + 1, width)],
             pixels_vector[coord_to_flat(0, j + 1, width)]])
        for j in range(1, height - 1)]
    refinements_right = [
        refine_pixel(
            pixels_vector[coord_to_flat(width - 1, j, width)],
            [pixels_vector[coord_to_flat(width - 1, j - 1, width)],
             pixels_vector[coord_to_flat(width - 2, j - 1, width)],
             pixels_vector[coord_to_flat(width - 2, j, width)],
             pixels_vector[coord_to_flat(width - 2, j + 1, width)],
             pixels_vector[coord_to_flat(width - 1, j + 1, width)]])
        for j in range(1, height - 1)]
    refinements_center = [
        refine_pixel(
            pixels_vector[coord_to_flat(i, j, width)],
            [pixels_vector[coord_to_flat(i - 1, j - 1, width)],
             pixels_vector[coord_to_flat(i, j - 1, width)],
             pixels_vector[coord_to_flat(i + 1, j - 1, width)],
             pixels_vector[coord_to_flat(i + 1, j, width)],
             pixels_vector[coord_to_flat(i + 1, j + 1, width)],
             pixels_vector[coord_to_flat(i, j + 1, width)],
             pixels_vector[coord_to_flat(i - 1, j + 1, width)],
             pixels_vector[coord_to_flat(i - 1, j, width)]])
        for j in range(1, height - 1) for i in range(1, width - 1)]

    # Generate output pixels, count refined and collect refined coordinates.
    refinement.add(refinement_top_left, top_left_is_refined, 0, 0)
    for index_pixel, (refined_pixel, pixel_is_refined) in enumerate(refinements_top):
        refinement.add(refined_pixel, pixel_is_refined, index_pixel + 1, 0)
    refinement.add(refinement_top_right, top_right_is_refined, width - 1, 0)
    for j in range(1, height - 1):
        refined_pixel_left, left_pixel_is_refined = refinements_left[j - 1]
        refinement.add(refined_pixel_left, left_pixel_is_refined, 0, j)
        for index_pixel_center in range((j - 1) * (width - 2), j * (width - 2)):
            refined_pixel, pixel_is_refined = refinements_center[index_pixel_center]
            local_x, local_y = flat_to_coord(index_pixel_center, width - 2)
            refinement.add(refined_pixel, pixel_is_refined, local_x + 1, local_y + 1)
        refined_pixel_right, pixel_right_is_refined = refinements_right[j - 1]
        refinement.add(refined_pixel_right, pixel_right_is_refined, width - 1, j)
    refinement.add(refinement_bottom_left, bottom_left_is_refined, 0, height - 1)
    for index_pixel, (refined_pixel, pixel_is_refined) in enumerate(refinements_bottom):
        refinement.add(refined_pixel, pixel_is_refined, index_pixel + 1, height - 1)
    refinement.add(refinement_bottom_right, bottom_right_is_refined, width - 1, height - 1)

    refinement.optimize()
    return refinement.output, refinement.nb_refined


def get_pixel_group(coordinates_to_pixel, pixel, x, y, width, height):
    coordinates = (x, y)
    del coordinates_to_pixel[coordinates]
    group = [coordinates]
    to_visit = positions_around(x, y, width, height)
    while to_visit:
        other_coordinates = to_visit[-1]
        del to_visit[-1]
        if other_coordinates in coordinates_to_pixel and coordinates_to_pixel[other_coordinates] == pixel:
            del coordinates_to_pixel[other_coordinates]
            group.append(other_coordinates)
            for position in positions_around(other_coordinates[0], other_coordinates[1], width, height):
                if position in coordinates_to_pixel:
                    to_visit.append(position)
    return group


def refine_groups(pixels, width, height):
    coordinates_to_group_id = {}
    groups = []
    coordinates_to_pixel = {flat_to_coord(index_pixel, width): pixel for index_pixel, pixel in enumerate(pixels)}
    while coordinates_to_pixel:
        (x, y), pixel = next(iter(coordinates_to_pixel.items()))
        group = get_pixel_group(coordinates_to_pixel, pixel, x, y, width, height)
        groups.append(group)
        for coordinates in group:
            coordinates_to_group_id[coordinates] = len(groups) - 1
    print(len(groups), 'pixels group(s).')
    output = []
    nb_refined = 0
    for index_pixel, pixel in enumerate(pixels):
        x, y = flat_to_coord(index_pixel, width)
        pixel_group_id = coordinates_to_group_id[(x, y)]
        local_groups = {coordinates_to_group_id[(x, y)]: 1}
        local_groups_weights = {}
        for other_coordinates in positions_around(x, y, width, height):
            other_group_id = coordinates_to_group_id[other_coordinates]
            local_groups.setdefault(other_group_id, 0)
            local_groups[other_group_id] += 1
        for group_id, n in local_groups.items():
            local_groups_weights[group_id] = n * math.log(len(groups[group_id]))
        max_groups = []
        max_count = None
        for group_id, group_weight in local_groups_weights.items():
            if max_count is None or max_count < group_weight:
                max_count = group_weight
                max_groups.clear()
                max_groups.append(group_id)
            elif max_count == group_weight:
                max_groups.append(group_id)
        if pixel_group_id in max_groups:
            selected_group_id = pixel_group_id
        elif len(max_groups) == 1:
            selected_group_id = max_groups[0]
            nb_refined += 1
        else:
            selected_group_id = sorted(max_groups)[0]
            nb_refined += 1
        chosen_x, chosen_y = groups[selected_group_id][0]
        group_color = pixels[coord_to_flat(chosen_x, chosen_y, width)]
        output.append(group_color)
    return output, nb_refined


def save_image(mode, size, data, name):
    output_image = Image.new(mode=mode, size=size, color=0)
    output_image.putdata(data)
    output_image.save(name)
    return output_image


def align_python(array_1, array_2):
    nb_rows = len(array_1)
    nb_cols = len(array_1[0])
    aligner = Aligner()
    total_score = 0
    matrix = [([0] * (1 + nb_cols)) for _ in range(1 + nb_rows)]
    for i in range(1 + nb_cols):
        matrix[0][i] = i * aligner.gap_score
    for i in range(nb_rows):
        total_score += aligner.align(array_1[i], array_2[i], score_only=True, matrix=matrix)
    n_cells = nb_rows * nb_cols
    min_val = min(aligner.match_score, aligner.diff_score, aligner.gap_score) * n_cells
    max_val = max(aligner.match_score, aligner.diff_score, aligner.gap_score) * n_cells
    return (total_score - min_val) / (max_val - min_val)


def classify_pixel(pixel, l, k):
    n = (l - 1) // k - 1
    pixel_class = []
    for v in pixel:
        if v % (n + 1) == 0:
            c = v
        else:
            i = int(v / (n + 1))
            p1 = i * (n + 1)
            p2 = (i + 1) * (n + 1)
            d1 = v - p1
            d2 = p2 - v
            if d1 <= d2:
                c = p1
            else:
                c = p2
        pixel_class.append(c)
    return tuple(pixel_class)


def simplify(image, threshold):
    alphabet_size = 256
    k = threshold
    assert isinstance(k, int)
    assert (alphabet_size - 1) % k == 0
    assert k <= alphabet_size - 1
    output = []
    for pixel in image.getdata():
        output.append(classify_pixel(pixel, alphabet_size, k))
    return output


def main():
    arguments = sys.argv[1:]
    assert len(arguments) in (1, 2)
    file_name = arguments[0]
    threshold = int(arguments[1]) if len(arguments) == 2 else PIXEL_DISTANCE_TRESHOLD
    image = ImageComparator.open_rgb_image(file_name)
    output = simplify(image, threshold)
    save_image(ImageComparator.WORK_MODE, image.size, output, 'simplification.png')
    refined, nb_refined = refine(output, image.width, image.height)
    save_image(ImageComparator.WORK_MODE, image.size, refined, 'simplification_refined.png')
    go, nr = refine_groups(refined, image.width, image.height)
    print('(1)', nr, 'group-refined')
    for i in range(5):
        go, nr = refine_groups(go, image.width, image.height)
        print('(%d)' % (i + 2), nr, 'group-refined')
    save_image(ImageComparator.WORK_MODE, image.size, go, 'group_refined.png')
    # x = get_segmentation(output_image, threshold)
    # save_image('L', image.size, x, 'segmentation.png')
    # rx = get_segmentation(refined_image, threshold)
    # save_image('L', image.size, rx, 'segmentation_refined.png')


if __name__ == '__main__':
    main()
