import os
from ctypes import c_char_p, pointer
from typing import List, Optional

from pysaurus.core.utils.classes import System
from pysaurus.core.video_raptor.functions import (PtrPtrVideoInfo, PtrPtrVideoThumbnail, PtrVideoInfo,
                                                  PtrVideoThumbnail, fn_ErrorReader_init, fn_ErrorReader_next,
                                                  fn_VideoInfo_clear, fn_VideoInfo_init, fn_VideoRaptorInfo_clear,
                                                  fn_VideoRaptorInfo_init, fn_VideoReport_hasError,
                                                  fn_VideoReport_isDone, fn_VideoThumbnail_init,
                                                  fn_videoRaptorDetails, fn_videoRaptorThumbnails)
from pysaurus.core.video_raptor.structures import ErrorReader, VideoInfo, VideoRaptorInfo, VideoThumbnail

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
    fn_VideoRaptorInfo_init(ptr_info)
    if info.hardwareDevicesCount:
        device_names = info.hardwareDevicesNames.decode().split(', ')
    fn_VideoRaptorInfo_clear(ptr_info)
    return device_names


def get_video_info_errors(report):
    error_strings = []
    if fn_VideoReport_hasError(pointer(report)):
        error_reader = ErrorReader()
        ptr_error_reader = pointer(error_reader)
        fn_ErrorReader_init(ptr_error_reader, report.errors)
        while True:
            next_error_string = fn_ErrorReader_next(ptr_error_reader)
            if not next_error_string:
                break
            error_strings.append(next_error_string.decode())
        if report.errorDetail:
            error_strings.append('ERROR_DETAIL: %s' % report.errorDetail.decode())
    return error_strings


def _video_info_to_params(video_info: VideoInfo):
    return {'filename': (video_info.filename.decode() if video_info.filename else None),
            'title': (video_info.title.decode() if video_info.title else None),
            'container_format': (video_info.container_format.decode() if video_info.container_format else None),
            'audio_codec': (video_info.audio_codec.decode() if video_info.audio_codec else None),
            'video_codec': (video_info.video_codec.decode() if video_info.video_codec else None),
            'audio_codec_description': (video_info.audio_codec_description.decode()
                                        if video_info.audio_codec_description else None),
            'video_codec_description': (video_info.video_codec_description.decode()
                                        if video_info.video_codec_description else None),
            'width': video_info.width,
            'height': video_info.height, 'frame_rate_num': video_info.frame_rate_num,
            'frame_rate_den': video_info.frame_rate_den, 'sample_rate': video_info.sample_rate,
            'duration': video_info.duration, 'duration_time_base': video_info.duration_time_base,
            'size': video_info.size, 'audio_bit_rate': video_info.audio_bit_rate}


def collect_video_info(file_names):
    # type: (List[str]) -> List[VideoRaptorResult]

    if not file_names:
        return []

    output = [None] * len(file_names)  # type: List[Optional[VideoRaptorResult]]
    encoded_file_names = [file_name.encode() for file_name in file_names]
    video_info_objects = [VideoInfo() for _ in file_names]
    video_info_pointers = [pointer(v) for v in video_info_objects]
    array_type = PtrVideoInfo * len(file_names)
    array_object = array_type(*video_info_pointers)

    for i in range(len(file_names)):
        fn_VideoInfo_init(video_info_pointers[i], c_char_p(encoded_file_names[i]))

    fn_videoRaptorDetails(len(file_names), PtrPtrVideoInfo(array_object))

    for i in range(len(file_names)):
        video_info = video_info_objects[i]
        done = _video_info_to_params(video_info) if fn_VideoReport_isDone(pointer(video_info.report)) else None
        errors = get_video_info_errors(video_info.report)
        if done and errors:
            done['errors'] = errors
            errors = None
        output[i] = VideoRaptorResult(done=done, errors=errors)
        fn_VideoInfo_clear(video_info_pointers[i])

    return output


class VideoInfoCollector:
    __slots__ = ('buffer_size', 'video_info_objects', 'video_info_pointers', 'array_type', 'array_object')

    def __init__(self, buffer_size):
        self.buffer_size = buffer_size
        self.video_info_objects = [VideoInfo() for _ in range(buffer_size)]
        self.video_info_pointers = [pointer(v) for v in self.video_info_objects]
        self.array_type = PtrVideoInfo * buffer_size
        self.array_object = self.array_type(*self.video_info_pointers)

    def collect(self, file_names):
        # type: (List[str]) -> List[VideoRaptorResult]

        assert len(file_names) <= self.buffer_size
        output = [None] * len(file_names)  # type: List[Optional[VideoRaptorResult]]
        encoded_file_names = [file_name.encode() for file_name in file_names]

        for i in range(len(file_names)):
            fn_VideoInfo_init(self.video_info_pointers[i], c_char_p(encoded_file_names[i]))

        fn_videoRaptorDetails(len(file_names), PtrPtrVideoInfo(self.array_object))

        for i in range(len(file_names)):
            video_info = self.video_info_objects[i]
            done = _video_info_to_params(video_info) if fn_VideoReport_isDone(pointer(video_info.report)) else None
            errors = get_video_info_errors(video_info.report)
            if done and errors:
                done['errors'] = errors
                errors = None
            output[i] = VideoRaptorResult(done=done, errors=errors)
            fn_VideoInfo_clear(self.video_info_pointers[i])

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
    array_type = PtrVideoThumbnail * len(file_names)
    array_object = array_type(*video_thumb_pointers)

    for i in range(len(file_names)):
        fn_VideoThumbnail_init(
            video_thumb_pointers[i],
            c_char_p(encoded_file_names[i]),
            c_char_p(encoded_output_folder),
            c_char_p(encoded_thumb_names[i])
        )

    fn_videoRaptorThumbnails(len(file_names), PtrPtrVideoThumbnail(array_object))

    for i in range(len(file_names)):
        video_thumb = video_thumb_objects[i]
        output[i] = VideoRaptorResult(
            done=fn_VideoReport_isDone(pointer(video_thumb.report)),
            errors=get_video_info_errors(video_thumb.report),
        )

    return output
