import argparse

from pysaurus.wip import image_utils
from pysaurus.wip.pillow_wip import classify_pixel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, required=True)
    parser.add_argument('--output', '-o', type=str, required=True)
    args = parser.parse_args()
    image = image_utils.open_rgb_image(args.input)
    width, height = image.size
    output = []
    for pixel in image.getdata():
        # output.append(pixel_class_to_value(pixel_class(*pixel)))
        output.append(classify_pixel(pixel, 256, 5))
    image_utils.save_rgb_image(width, height, output, args.output)


if __name__ == '__main__':
    main()
