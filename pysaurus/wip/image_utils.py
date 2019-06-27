import sys
from typing import List

from PIL import Image

from pysaurus.core.profiling import Profiler
from pysaurus.core.video_raptor import api as video_raptor
from pysaurus.wip.aligner import Aligner


class ImageComparator:
    __slots__ = ('aligner',)
    WORK_MODE = 'RGB'
    THUMBNAIL_SIZE = (32, 32)

    def __init__(self):
        self.aligner = Aligner()

    def align(self, array_1, array_2):
        # type: (List[List[int]], List[List[int]]) -> float
        nb_rows = len(array_1)
        total_score = video_raptor.align_integer_sequences(
            array_1, array_2, self.aligner.match_score, self.aligner.diff_score, self.aligner.gap_score)
        n_cells = nb_rows * len(array_1[0])
        min_val = min(self.aligner.match_score, self.aligner.diff_score, self.aligner.gap_score) * n_cells
        max_val = max(self.aligner.match_score, self.aligner.diff_score, self.aligner.gap_score) * n_cells
        return (total_score - min_val) / (max_val - min_val)

    def align_by_diff(self, array_1, array_2):
        # type: (List[List[int]], List[List[int]]) -> float
        nb_rows = len(array_1)
        total_score = video_raptor.align_integer_sequences_by_diff(array_1, array_2, 0, 255, self.aligner.gap_score)
        n_cells = nb_rows * len(array_1[0])
        min_val = min(-1, 1, self.aligner.gap_score) * n_cells
        max_val = max(-1, 1, self.aligner.gap_score) * n_cells
        return (total_score - min_val) / (max_val - min_val)

    @staticmethod
    def open_image(file_name):
        image = Image.open(file_name)
        if image.mode != ImageComparator.WORK_MODE:
            image = image.convert(ImageComparator.WORK_MODE)
        return image

    @staticmethod
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

    @staticmethod
    def simplify(image, threshold):
        alphabet_size = 256
        k = threshold
        assert isinstance(k, int)
        assert (alphabet_size - 1) % k == 0
        assert k <= alphabet_size - 1
        output = []
        for pixel in image.getdata():
            output.append(ImageComparator.classify_pixel(pixel, alphabet_size, k))
        return output

    @staticmethod
    def to_gray_array(image, threshold=3):
        iterable = ImageComparator.simplify(image, threshold=threshold) if threshold > 0 else image.getdata()
        inline_output = [int(sum(pixel) / 3) for pixel in iterable]
        inline_output_length = len(inline_output)
        output = []
        width = image.size[0]
        cursor = 0
        while cursor < inline_output_length:
            output.append(inline_output[cursor:(cursor + width)])
            cursor += width
        return output

    @staticmethod
    def to_thumbnail_gray_array(file_name, threshold=3):
        image = ImageComparator.open_image(file_name)
        thumbnail = image.resize(ImageComparator.THUMBNAIL_SIZE)
        return ImageComparator.to_gray_array(thumbnail, threshold=threshold)


def main():
    image_comparator = ImageComparator()
    if len(sys.argv) != 3:
        exit(-1)
    file_name_1 = sys.argv[1]
    file_name_2 = sys.argv[2]
    output_1 = image_comparator.to_thumbnail_gray_array(file_name_1)
    output_2 = image_comparator.to_thumbnail_gray_array(file_name_2)
    with Profiler('align'):
        print(image_comparator.align(output_1, output_2))


if __name__ == '__main__':
    main()
