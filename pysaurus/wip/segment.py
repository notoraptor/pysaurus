import sys
import math
from pysaurus.wip import image_utils


def classify(pixel):
    r, g, b = pixel
    if r > g == b: return (255, 0, 0)
    if g > r == b: return (0, 255, 0)
    if b > r == g: return (0, 0, 255)
    if r == g > b: return (255, 255, 0)
    if r == b > g: return (255, 0, 255)
    if g == b > r: return (0, 255, 255)
    if r == g == b: return (128, 128, 128)
    if r > g > b: return (255, 170, 85)
    if r > b > g: return (255, 85, 170)
    if g > r > b: return (170, 255, 85)
    if g > b > r: return (85, 255, 170)
    if b > r > g: return (170, 85, 255)
    if b > g > r: return (85, 170, 255)


def main():
    if len(sys.argv) != 2:
        return
    filename = sys.argv[1]
    image = image_utils.open_rgb_image(filename)
    width, height = image.size
    data = list(image.getdata())
    distances = []
    for i, pixel in enumerate(data):
        r, g, b = data[i]
        x, y = image_utils.flat_to_coord(i, width)
        for x_around, y_around in (
                (x - 1, y - 1),
                (x, y - 1),
                (x + 1, y - 1),
                (x - 1, y),
                (x + 1, y),
                (x - 1, y + 1),
                (x, y + 1),
                (x + 1, y + 1),
        ):
            if 0 <= x_around < width and 0 <= y_around < height:
                other_r, other_g, other_b = data[image_utils.coord_to_flat(x_around, y_around, width)]
                distances.append(math.sqrt((r - other_r) ** 2 + (g - other_g) ** 2 + (b - other_b) ** 2))
    distances.sort()
    max_distance = 255 * math.sqrt(3)
    len_distances = len(distances)
    if len_distances % 2 == 0:
        pivot = len_distances // 2
        value_before = distances[pivot - 1]
        value_after = distances[pivot]
        average_distance = (value_before + value_after) / 2
    else:
        pivot = ((len_distances - 1) // 2)
        average_distance = distances[pivot]
    print(average_distance)
    output = []
    for i, (r, g, b) in enumerate(data):
        if i % width == 0:
            output.append((255, 255, 255))
            continue
        other_r, other_g, other_b = data[i - 1]
        distance = math.sqrt((r - other_r) ** 2 + (g - other_g) ** 2 + (b - other_b) ** 2)
        gray = int(255 * (max_distance - distance) / max_distance)
        output.append((gray, gray, gray))
        # if distance >= average_distance:
        #     gray = int(255 * distance / max_distance)
        #     output.append((gray, gray, gray))
        # else:
        #     output.append((255, 255, 255))
    image_utils.save_rgb_image(width, height, output, 'test.jpg')


if __name__ == '__main__':
    main()
