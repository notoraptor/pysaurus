import base64
from ctypes import c_double, c_int, memset, pointer, sizeof
from typing import Any, Iterable, List, Optional, Tuple

from pysaurus.core.constants import VIDEO_BATCH_SIZE
from pysaurus.core.modules import ImageUtils
from pysaurus.core.native.video_raptor.symbols import (PtrPtrSequence, PtrSequence, Sequence,
                                                       c_int_p, fn_classifySimilarities)
from pysaurus.core.profiling import Profiler


class Miniature:
    __slots__ = ('identifier', 'r', 'g', 'b', 'i', 'width', 'height')

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (List[int], List[int], List[int], int, int, Any) -> None
        self.r = red
        self.g = green
        self.b = blue
        self.i = None
        self.width = width
        self.height = height
        self.identifier = identifier

    @property
    def size(self):
        return self.width * self.height

    def coordinates_around(self, x, y, radius=1):
        coordinates = []
        for local_x in range(max(0, x - radius), min(x + radius, self.width - 1) + 1):
            for local_y in range(max(0, y - radius), min(y + radius, self.height - 1) + 1):
                coordinates.append((local_x, local_y))
        return coordinates

    def tuples(self):
        for i in range(len(self.r)):
            yield (self.r[i], self.g[i], self.b[i])

    def to_c_sequence(self, score=0.0, classification=-1):
        array_type = c_int * len(self.r)
        return Sequence(c_int_p(array_type(*self.r)),
                        c_int_p(array_type(*self.g)),
                        c_int_p(array_type(*self.b)),
                        None if self.i is None else c_int_p(array_type(*self.i)),
                        score, classification)

    def to_dict(self):
        return {
            'r': base64.b64encode(bytearray(self.r)),
            'g': base64.b64encode(bytearray(self.g)),
            'b': base64.b64encode(bytearray(self.b)),
            'w': self.width,
            'h': self.height,
            'i': self.identifier,
        }

    @staticmethod
    def from_dict(dct):
        return Miniature(red=[int(v) for v in base64.b64decode(dct['r'])],
                         green=[int(v) for v in base64.b64decode(dct['g'])],
                         blue=[int(v) for v in base64.b64decode(dct['b'])],
                         width=dct['w'],
                         height=dct['h'],
                         identifier=dct['i'])

    @staticmethod
    def from_file_name(file_name, dimensions, identifier=None):
        # type: (str, Tuple[int, int], Optional[Any]) -> Miniature
        image = ImageUtils.open_rgb_image(file_name)
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


def classify_similarities(miniatures):
    # type: (List[Miniature]) -> Iterable[float]
    nb_sequences = len(miniatures)
    native_sequences = [sequence.to_c_sequence() for i, sequence in enumerate(miniatures)]
    native_sequence_pointers = [pointer(sequence) for sequence in native_sequences]
    pointer_array_type = PtrSequence * nb_sequences
    native_edges = (c_double * (nb_sequences * nb_sequences))()
    memset(native_edges, 0, sizeof(native_edges))
    # assert all(s.classification == -1 for s in native_sequences)
    with Profiler('Finding similar images using simpler NATIVE comparison.'):
        cursor = 0
        while cursor < nb_sequences:
            i_from = cursor
            i_to = cursor + VIDEO_BATCH_SIZE
            print('[%s;%s[/%s' % (i_from, i_to, nb_sequences))
            fn_classifySimilarities(
                PtrPtrSequence(pointer_array_type(*native_sequence_pointers)), nb_sequences,
                i_from, i_to, miniatures[0].width, miniatures[0].height, native_edges)
            cursor = i_to
    return native_edges
