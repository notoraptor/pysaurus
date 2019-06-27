import os
from ctypes import pointer, c_char_p, c_int
from typing import List, Optional

from pysaurus.core.database.video import Video
from pysaurus.core.utils.classes import System
from pysaurus.core.video_raptor.functions import (__fn_VideoRaptorInfo_init, __fn_VideoRaptorInfo_clear,
                                                  __fn_VideoReport_hasError, __fn_ErrorReader_init,
                                                  __fn_ErrorReader_next, __PtrVideoInfo, __fn_VideoInfo_init,
                                                  __fn_videoRaptorDetails, __PtrPtrVideoInfo, __fn_VideoReport_isDone,
                                                  __fn_VideoInfo_clear, __PtrVideoThumbnail,
                                                  __fn_VideoThumbnail_init, __fn_videoRaptorThumbnails,
                                                  __PtrPtrVideoThumbnail, __fn_batchAlignmentScore, __PtrPtrInt,
                                                  __PtrInt,
                                                  __fn_batchAlignmentScoreByDiff)
from pysaurus.core.video_raptor.structures import VideoRaptorInfo, ErrorReader, VideoInfo, VideoThumbnail

if System.is_linux():
    # Trying to prevent this warning on Ubuntu:
    # Failed to open VDPAU backend libvdpau_.so: cannot open shared object file: No such file or directory
    os.environ['VDPAU_DRIVER'] = 'va_gl'


class VideoRaptorResult:
    __slots__ = ('done', 'errors')

    def __init__(self, *, done=None, errors=None):
        self.done = done
        self.errors = errors

    def __str__(self):
        if self.done:
            return str(self.done)
        return str(self.errors)


def get_hardware_device_names():
    device_names = []
    info = VideoRaptorInfo()
    ptr_info = pointer(info)
    __fn_VideoRaptorInfo_init(ptr_info)
    if info.hardwareDevicesCount:
        device_names = info.hardwareDevicesNames.decode().split(', ')
    __fn_VideoRaptorInfo_clear(ptr_info)
    return device_names


def get_video_info_errors(report):
    error_strings = []
    if __fn_VideoReport_hasError(pointer(report)):
        error_reader = ErrorReader()
        ptr_error_reader = pointer(error_reader)
        __fn_ErrorReader_init(ptr_error_reader, report.errors)
        while True:
            next_error_string = __fn_ErrorReader_next(ptr_error_reader)
            if not next_error_string:
                break
            error_strings.append(next_error_string.decode())
        if report.errorDetail:
            error_strings.append('ERROR_DETAIL: %s' % report.errorDetail.decode())
    return error_strings


def collect_video_info(file_names: list):
    if not file_names:
        return

    output = [None] * len(file_names)  # type: List[Optional[VideoRaptorResult]]
    encoded_file_names = [file_name.encode() for file_name in file_names]
    video_info_objects = [VideoInfo() for _ in file_names]
    video_info_pointers = [pointer(v) for v in video_info_objects]
    array_type = __PtrVideoInfo * len(file_names)
    array_object = array_type(*video_info_pointers)

    for i in range(len(file_names)):
        __fn_VideoInfo_init(video_info_pointers[i], c_char_p(encoded_file_names[i]))

    __fn_videoRaptorDetails(len(file_names), __PtrPtrVideoInfo(array_object))

    for i in range(len(file_names)):
        video_info = video_info_objects[i]
        output[i] = VideoRaptorResult(
            done=(Video.from_video_info(video_info) if __fn_VideoReport_isDone(pointer(video_info.report)) else None),
            errors=get_video_info_errors(video_info.report)
        )
        __fn_VideoInfo_clear(video_info_pointers[i])

    return output


def generate_video_thumbnails(file_names: list, thumb_names: list, output_folder: str):
    if not file_names:
        return

    output = [None] * len(file_names)  # type: List[Optional[VideoRaptorResult]]
    encoded_file_names = [file_name.encode() for file_name in file_names]
    encoded_thumb_names = [thumb_name.encode() for thumb_name in thumb_names]
    encoded_output_folder = output_folder.encode()

    video_thumb_objects = [VideoThumbnail() for _ in file_names]
    video_thumb_pointers = [pointer(v) for v in video_thumb_objects]
    array_type = __PtrVideoThumbnail * len(file_names)
    array_object = array_type(*video_thumb_pointers)

    for i in range(len(file_names)):
        __fn_VideoThumbnail_init(
            video_thumb_pointers[i],
            c_char_p(encoded_file_names[i]),
            c_char_p(encoded_output_folder),
            c_char_p(encoded_thumb_names[i])
        )

    __fn_videoRaptorThumbnails(len(file_names), __PtrPtrVideoThumbnail(array_object))

    for i in range(len(file_names)):
        video_thumb = video_thumb_objects[i]
        output[i] = VideoRaptorResult(
            done=__fn_VideoReport_isDone(pointer(video_thumb.report)),
            errors=get_video_info_errors(video_thumb.report),
        )

    return output


def align_integer_sequences(sequences_1, sequences_2, match_score, diff_score, gap_score):
    n_rows = len(sequences_1)
    n_cols = len(sequences_1[0])
    line_type = c_int * n_cols
    array_type = __PtrInt * n_rows
    return __fn_batchAlignmentScore(
        __PtrPtrInt(array_type(*[line_type(*line) for line in sequences_1])),
        __PtrPtrInt(array_type(*[line_type(*line) for line in sequences_2])),
        n_rows, n_cols, match_score, diff_score, gap_score
    )


def align_integer_sequences_by_diff(sequences_1, sequences_2, width, height, min_val, max_val, gap_score):
    line_type = c_int * (width * height)
    return __fn_batchAlignmentScoreByDiff(
        __PtrInt(line_type(*sequences_1)),
        __PtrInt(line_type(*sequences_2)),
        height, width, min_val, max_val, gap_score
    )
