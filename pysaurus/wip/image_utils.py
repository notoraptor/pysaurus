import sys
from typing import Any, Optional

from PIL import Image

from pysaurus.core.profiling import Profiler
from pysaurus.core.video_raptor import alignment as native_alignment
from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.wip.aligner import Aligner


class ImageComparator:
    __slots__ = ('aligner', 'min_thumb_score_by_diff', 'max_thumb_score_by_diff',
                 'width', 'height', 'min_val', 'max_val')
    WORK_MODE = 'RGB'
    GRAY_MODE = 'L'
    THUMBNAIL_SIZE = (32, 32)

    def __init__(self):
        aligner = Aligner()
        self.width, self.height = self.THUMBNAIL_SIZE
        size = self.width * self.height
        unit_scores_by_diff = (-1, 1, aligner.gap_score)
        self.aligner = aligner
        self.min_thumb_score_by_diff = min(unit_scores_by_diff) * size
        self.max_thumb_score_by_diff = max(unit_scores_by_diff) * size
        self.min_val = 0
        self.max_val = 255

    def align_channels_by_diff(self, miniature_1, miniature_2):
        # type: (Miniature, Miniature) -> float
        v_gap = self.aligner.gap_score
        score_r = native_alignment.align_integer_sequences(
            miniature_1.r, miniature_2.r, self.width, self.height, self.min_val, self.max_val, v_gap)
        score_g = native_alignment.align_integer_sequences(
            miniature_1.g, miniature_2.g, self.width, self.height, self.min_val, self.max_val, v_gap)
        score_b = native_alignment.align_integer_sequences(
            miniature_1.b, miniature_2.b, self.width, self.height, self.min_val, self.max_val, v_gap)
        return (score_r + score_g + score_b - 3 * self.min_thumb_score_by_diff) / (
                3 * (self.max_thumb_score_by_diff - self.min_thumb_score_by_diff))

    @staticmethod
    def open_rgb_image(file_name):
        image = Image.open(file_name)
        if image.mode != ImageComparator.WORK_MODE:
            image = image.convert(ImageComparator.WORK_MODE)
        return image

    @staticmethod
    def to_miniature(file_name, identifier=None):
        # type: (str, Optional[Any]) -> Miniature
        image = ImageComparator.open_rgb_image(file_name)
        thumbnail = image.resize(ImageComparator.THUMBNAIL_SIZE)
        width, height = ImageComparator.THUMBNAIL_SIZE
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
    return save_image(ImageComparator.GRAY_MODE, (width, height), data, name)


def save_rgb_image(width, height, data, name):
    return save_image(ImageComparator.WORK_MODE, (width, height), data, name)


def main():
    image_comparator = ImageComparator()
    if len(sys.argv) != 3:
        exit(-1)
    file_name_1 = sys.argv[1]
    file_name_2 = sys.argv[2]
    output_1 = image_comparator.to_miniature(file_name_1)
    output_2 = image_comparator.to_miniature(file_name_2)
    with Profiler('align'):
        print(image_comparator.align_channels_by_diff(output_1, output_2))


if __name__ == '__main__':
    main()