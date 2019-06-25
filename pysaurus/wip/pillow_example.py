import sys
from pysaurus.wip.aligner import Aligner
from pysaurus.core.profiling import Profiler
from pysaurus.core.video_raptor import api as video_raptor

from PIL import Image

WORK_MODE = 'RGB'


def open_image(file_name):
    image = Image.open(file_name)
    if image.mode != WORK_MODE:
        image = image.convert(WORK_MODE)
    return image


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


def to_gray_array(image, threshold=3):
    inline_output = []
    iterable = simplify(image, threshold=threshold) if threshold > 0 else image.getdata()
    for pixel in iterable:
        inline_output.append(int(sum(pixel)/3))
    output = []
    inline_output_length = len(inline_output)
    width = image.size[0]
    cursor = 0
    while cursor < inline_output_length:
        output.append(inline_output[cursor:(cursor + width)])
        cursor += width
    return output


def save_image(mode, size, data, name):
    output_image = Image.new(mode=mode, size=size, color=0)
    output_image.putdata(data)
    output_image.save(name)
    return output_image


def to_thumbnail_gray_array(file_name, threshold=3):
    thumbnail_size = (128, 128)
    image = open_image(file_name)
    thumbnail = image.resize(thumbnail_size)
    return to_gray_array(thumbnail, threshold=threshold)


def align(array_1, array_2):
    nb_rows = len(array_1)
    aligner = Aligner()
    total_score = video_raptor.align_integer_sequences(
        array_1, array_2, aligner.match_score, aligner.diff_score, aligner.gap_score)
    n_cells = nb_rows * len(array_1[0])
    min_val = min(aligner.match_score, aligner.diff_score, aligner.gap_score) * n_cells
    max_val = max(aligner.match_score, aligner.diff_score, aligner.gap_score) * n_cells
    return (total_score - min_val) / (max_val - min_val)


def align_by_diff(array_1, array_2):
    nb_rows = len(array_1)
    aligner = Aligner(in_del=0)
    total_score = video_raptor.align_integer_sequences_by_diff(array_1, array_2, 0, 255, aligner.gap_score)
    n_cells = nb_rows * len(array_1[0])
    min_val = min(-1, 1, aligner.gap_score) * n_cells
    max_val = max(-1, 1, aligner.gap_score) * n_cells
    return (total_score - min_val) / (max_val - min_val)


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


def main():
    if len(sys.argv) != 3:
        exit(-1)
    file_name_1 = sys.argv[1]
    file_name_2 = sys.argv[2]
    output_1 = to_thumbnail_gray_array(file_name_1)
    output_2 = to_thumbnail_gray_array(file_name_2)
    raw_output_1 = to_thumbnail_gray_array(file_name_1, threshold=0)
    raw_output_2 = to_thumbnail_gray_array(file_name_2, threshold=0)
    with Profiler('align_by_diff'):
        print(align_by_diff(raw_output_1, raw_output_2))
    with Profiler('align'):
        print(align(output_1, output_2))
    with Profiler('align_python'):
        print(align_python(output_1, output_2))


if __name__ == '__main__':
    main()