import math

from PIL import Image

IMAGE_RGB_MODE = 'RGB'
IMAGE_GRAY_MODE = 'L'
DEFAULT_THUMBNAIL_SIZE = (32, 32)
MAX_PIXEL_DISTANCE = 255 * math.sqrt(3)


def __save_image(mode, size, data, name):
    output_image = Image.new(mode=mode, size=size, color=0)
    output_image.putdata(data)
    output_image.save(name)
    return output_image


def open_rgb_image(file_name):
    image = Image.open(file_name)
    if image.mode != IMAGE_RGB_MODE:
        image = image.convert(IMAGE_RGB_MODE)
    return image


def save_gray_image(width, height, data, name):
    # Data must be a list of gray values in [0; 255].
    return __save_image(IMAGE_GRAY_MODE, (width, height), data, name)


def save_rgb_image(width, height, data, name):
    # Data must be a list of triples (r, g, b), each in [0; 255].
    return __save_image(IMAGE_RGB_MODE, (width, height), data, name)


def flat_to_coord(index_pixel, width):
    # i => (x, y)
    return index_pixel % width, index_pixel // width


def coord_to_flat(x, y, width):
    # (x, y) => i
    return y * width + x
