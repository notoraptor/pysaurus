from typing import Any, Optional, Tuple

from PIL import Image

from pysaurus.core.video_raptor.alignment_utils import Miniature

IMAGE_RGB_MODE = 'RGB'
IMAGE_GRAY_MODE = 'L'
DEFAULT_THUMBNAIL_SIZE = (32, 32)


def open_rgb_image(file_name):
    image = Image.open(file_name)
    if image.mode != IMAGE_RGB_MODE:
        image = image.convert(IMAGE_RGB_MODE)
    return image


def image_to_miniature(file_name, dimensions, identifier=None):
    # type: (str, Tuple[int, int], Optional[Any]) -> Miniature
    image = open_rgb_image(file_name)
    thumbnail = image.resize(dimensions)
    width, height = dimensions
    size = width * height
    red = [0] * size
    green = [0] * size
    blue = [0] * size
    for i, (r, g, b) in enumerate(thumbnail.getdata()):
        red[i] = r
        green[i] = g
        blue[i] = b
    return Miniature(red, green, blue, width, height, identifier)


def save_image(mode, size, data, name):
    output_image = Image.new(mode=mode, size=size, color=0)
    output_image.putdata(data)
    output_image.save(name)
    return output_image


def save_gray_image(width, height, data, name):
    # Data must be a list of gray values in [0; 255].
    return save_image(IMAGE_GRAY_MODE, (width, height), data, name)


def save_rgb_image(width, height, data, name):
    # Data must be a list of triples (r, g, b), each in [0; 255].
    return save_image(IMAGE_RGB_MODE, (width, height), data, name)


def flat_to_coord(index_pixel, width):
    # i => (x, y)
    return index_pixel % width, index_pixel // width


def coord_to_flat(x, y, width):
    # (x, y) => i
    return y * width + x