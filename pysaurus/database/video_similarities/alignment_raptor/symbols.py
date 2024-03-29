from ctypes import POINTER, Structure, c_double, c_int

from pysaurus.bin.symbols import ALIGNMENT_RAPTOR
from pysaurus.core.native.clibrary import CLibrary, c_bool_p, c_double_p, c_int_p


class Sequence(Structure):
    _fields_ = [
        ("r", c_int_p),
        ("g", c_int_p),
        ("b", c_int_p),
        ("i", c_int_p),
        ("score", c_double),
        ("classification", c_int),
    ]


PtrSequence = POINTER(Sequence)
PtrPtrSequence = POINTER(PtrSequence)

_dll_video_raptor = CLibrary(ALIGNMENT_RAPTOR.path)

fn_classifySimilarities = _dll_video_raptor.prototype(
    "classifySimilarities",
    None,
    [PtrPtrSequence, c_int, c_int, c_int, c_int, c_int, c_double_p],
)
fn_classifySimilaritiesDirected = _dll_video_raptor.prototype(
    "classifySimilaritiesDirected",
    None,
    [PtrPtrSequence, c_int, c_int, c_int, c_int, c_int, c_bool_p, c_double],
)

fn_classifySimilaritiesSelected = _dll_video_raptor.prototype(
    "classifySimilaritiesSelected",
    None,
    [PtrPtrSequence, c_int, c_int, c_int, c_int, c_int, c_double, c_int_p],
)

fn_compareSimilarSequences = _dll_video_raptor.prototype(
    "compareSimilarSequences", c_double, [PtrSequence, PtrSequence, c_int, c_int, c_int]
)
