from ctypes import (
    POINTER,
    Structure,
    c_bool,
    c_char,
    c_char_p,
    c_double,
    c_int,
    c_int64,
    c_size_t,
    c_uint,
    c_void_p,
)

from pysaurus.core.native.clibrary import CLibrary, c_int_p, c_double_p

ERROR_DETAIL_MAX_LENGTH = 64

c_char_array = POINTER(c_char_p)


class VideoRaptorInfo(Structure):
    _fields_ = [("hardwareDevicesCount", c_size_t), ("hardwareDevicesNames", c_char_p)]


PtrVideoRaptorInfo = POINTER(VideoRaptorInfo)


class ErrorReader(Structure):
    _fields_ = [
        ("errors", c_uint),
        ("position", c_uint),
    ]


PtrErrorReader = POINTER(ErrorReader)


class VideoReport(Structure):
    _fields_ = [("errors", c_uint), ("errorDetail", c_char * ERROR_DETAIL_MAX_LENGTH)]


PtrVideoReport = POINTER(VideoReport)
PtrPtrVideoReport = POINTER(PtrVideoReport)


class VideoInfo(Structure):
    _fields_ = [
        ("filename", c_char_p),
        ("title", c_char_p),
        ("container_format", c_char_p),
        ("audio_codec", c_char_p),
        ("video_codec", c_char_p),
        ("audio_codec_description", c_char_p),
        ("video_codec_description", c_char_p),
        ("width", c_int),
        ("height", c_int),
        ("frame_rate_num", c_int),
        ("frame_rate_den", c_int),
        ("sample_rate", c_int),
        ("duration", c_int64),
        ("duration_time_base", c_int64),
        ("size", c_int64),
        ("audio_bit_rate", c_int64),
        ("report", VideoReport),
        ("device_name", c_char_p),
    ]


PtrVideoInfo = POINTER(VideoInfo)


class VideoThumbnail(Structure):
    _fields_ = [
        ("filename", c_char_p),
        ("thumbnailFolder", c_char_p),
        ("thumbnailName", c_char_p),
        ("report", VideoReport),
    ]


PtrVideoThumbnail = POINTER(VideoThumbnail)
PtrPtrVideoInfo = POINTER(PtrVideoInfo)
PtrPtrVideoThumbnail = POINTER(PtrVideoThumbnail)
PtrPtrInt = POINTER(c_int_p)


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

_dll_video_raptor = CLibrary("videoRaptorBatch")

fn_VideoRaptorContextNew = _dll_video_raptor.prototype(
    "VideoRaptorContext_New", c_void_p, []
)
fn_VideoRaptorContextDelete = _dll_video_raptor.prototype(
    "VideoRaptorContext_Delete", None, [c_void_p]
)
fn_ErrorReader_init = _dll_video_raptor.prototype(
    "ErrorReader_init", None, [PtrErrorReader, c_uint]
)
fn_ErrorReader_next = _dll_video_raptor.prototype(
    "ErrorReader_next", c_char_p, [PtrErrorReader]
)
fn_VideoReport_isDone = _dll_video_raptor.prototype(
    "VideoReport_isDone", c_bool, [PtrVideoReport]
)
fn_VideoReport_hasError = _dll_video_raptor.prototype(
    "VideoReport_hasError", c_bool, [PtrVideoReport]
)
fn_VideoReport_hasDeviceError = _dll_video_raptor.prototype(
    "VideoReport_hasDeviceError", c_bool, [PtrVideoReport]
)
fn_VideoInfo_init = _dll_video_raptor.prototype(
    "VideoInfo_init", None, [PtrVideoInfo, c_char_p]
)
fn_VideoInfo_clear = _dll_video_raptor.prototype(
    "VideoInfo_clear", None, [PtrVideoInfo]
)
fn_VideoThumbnail_init = _dll_video_raptor.prototype(
    "VideoThumbnail_init", None, [PtrVideoThumbnail, c_char_p, c_char_p, c_char_p]
)
fn_videoRaptorDetails = _dll_video_raptor.prototype(
    "videoRaptorDetails", c_int, [c_void_p, c_int, PtrPtrVideoInfo]
)
fn_videoRaptorThumbnails = _dll_video_raptor.prototype(
    "videoRaptorThumbnails", c_int, [c_void_p, c_int, PtrPtrVideoThumbnail]
)
fn_videoRaptorJSON = _dll_video_raptor.prototype(
    "videoRaptorJSON",
    c_int,
    [c_void_p, c_int, c_char_array, PtrPtrVideoReport, c_char_p],
)
fn_batchAlignmentScore = _dll_video_raptor.prototype(
    "batchAlignmentScore",
    c_double,
    [c_int_p, c_int_p, c_int, c_int, c_int, c_int, c_int],
)
fn_classifySimilarities = _dll_video_raptor.prototype(
    "classifySimilarities",
    None,
    [PtrPtrSequence, c_int, c_int, c_int, c_int, c_int, c_double_p],
)
fn_classifySimilaritiesDirected = _dll_video_raptor.prototype(
    "classifySimilaritiesDirected",
    None,
    [PtrPtrSequence, c_int, c_int, c_int, c_int, c_int, c_double_p],
)
