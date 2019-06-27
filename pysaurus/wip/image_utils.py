import sys
from typing import Optional, Any

from PIL import Image

from pysaurus.core.profiling import Profiler
from pysaurus.core.video_raptor import api as video_raptor
from pysaurus.wip.aligner import Aligner


class ThumbnailChannels:
    __slots__ = ('identifier', 'r', 'g', 'b')

    def __init__(self, red, green, blue, identifier=None):
        self.r = red
        self.g = green
        self.b = blue
        self.identifier = identifier


class ImageComparator:
    __slots__ = ('aligner', 'min_thumb_score_by_diff', 'max_thumb_score_by_diff', 'width', 'height')
    WORK_MODE = 'RGB'
    THUMBNAIL_SIZE = (32, 32)

    def __init__(self):
        aligner = Aligner()
        self.width, self.height = self.THUMBNAIL_SIZE
        size = self.width * self.height
        unit_scores_by_diff = (-1, 1, aligner.gap_score)
        self.aligner = aligner
        self.min_thumb_score_by_diff = min(unit_scores_by_diff) * size
        self.max_thumb_score_by_diff = max(unit_scores_by_diff) * size

    def align_channels_by_diff(self, channels_1, channels_2):
        # type: (ThumbnailChannels, ThumbnailChannels) -> float
        v_min = 0
        v_max = 255
        v_gap = self.aligner.gap_score
        score_r = video_raptor.align_integer_sequences_by_diff(
            channels_1.r, channels_2.r, self.width, self.height, v_min, v_max, v_gap)
        score_g = video_raptor.align_integer_sequences_by_diff(
            channels_1.g, channels_2.g, self.width, self.height, v_min, v_max, v_gap)
        score_b = video_raptor.align_integer_sequences_by_diff(
            channels_1.b, channels_2.b, self.width, self.height, v_min, v_max, v_gap)
        return (score_r + score_g + score_b - 3 * self.min_thumb_score_by_diff) / (
                3 * (self.max_thumb_score_by_diff - self.min_thumb_score_by_diff))

    @staticmethod
    def open_rgb_image(file_name):
        image = Image.open(file_name)
        if image.mode != ImageComparator.WORK_MODE:
            image = image.convert(ImageComparator.WORK_MODE)
        return image

    @staticmethod
    def to_thumbnail_channels(file_name, identifier=None):
        # type: (str, Optional[Any]) -> ThumbnailChannels
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
        return ThumbnailChannels(red, green, blue, identifier)


def main():
    image_comparator = ImageComparator()
    if len(sys.argv) != 3:
        exit(-1)
    file_name_1 = sys.argv[1]
    file_name_2 = sys.argv[2]
    output_1 = image_comparator.to_thumbnail_channels(file_name_1)
    output_2 = image_comparator.to_thumbnail_channels(file_name_2)
    with Profiler('align'):
        print(image_comparator.align_channels_by_diff(output_1, output_2))


if __name__ == '__main__':
    main()
