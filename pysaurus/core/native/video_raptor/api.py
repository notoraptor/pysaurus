import os
from ctypes import c_char_p, pointer
from typing import List, Optional

from pysaurus.core.classes import ListView
from pysaurus.core.modules import System
from pysaurus.core.native.video_raptor import symbols

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
    info = symbols.VideoRaptorInfo()
    ptr_info = pointer(info)
    symbols.fn_VideoRaptorInfo_init(ptr_info)
    if info.hardwareDevicesCount:
        device_names = info.hardwareDevicesNames.decode().split(', ')
    symbols.fn_VideoRaptorInfo_clear(ptr_info)
    return device_names


def get_video_info_errors(report):
    error_strings = []
    if symbols.fn_VideoReport_hasError(pointer(report)):
        error_reader = symbols.ErrorReader()
        ptr_error_reader = pointer(error_reader)
        symbols.fn_ErrorReader_init(ptr_error_reader, report.errors)
        while True:
            next_error_string = symbols.fn_ErrorReader_next(ptr_error_reader)
            if not next_error_string:
                break
            error_strings.append(next_error_string.decode())
        if report.errorDetail:
            error_strings.append('ERROR_DETAIL: %s' % report.errorDetail.decode())
    return error_strings


def _info_to_params(video_info: symbols.VideoInfo):
    return {'filename': (video_info.filename.decode() if video_info.filename else None),
            'meta_title': (video_info.title.decode() if video_info.title else None),
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
            'size': video_info.size, 'audio_bit_rate': video_info.audio_bit_rate,
            'device_name': video_info.device_name}


class VideoInfoCollector:
    __slots__ = ('buffer_size', 'objects', 'pointers', 'array_type', 'array_object')

    def __init__(self, buffer_size):
        self.buffer_size = buffer_size
        self.objects = [symbols.VideoInfo() for _ in range(buffer_size)]
        self.pointers = [pointer(v) for v in self.objects]
        self.array_type = symbols.PtrVideoInfo * buffer_size
        self.array_object = self.array_type(*self.pointers)

    def collect(self, file_names):
        # type: (ListView[str]) -> List[VideoRaptorResult]

        assert len(file_names) <= self.buffer_size
        output = [None] * len(file_names)  # type: List[Optional[VideoRaptorResult]]
        encoded_file_names = [file_name.encode() for file_name in file_names]

        for i in range(len(file_names)):
            symbols.fn_VideoInfo_init(self.pointers[i], c_char_p(encoded_file_names[i]))

        symbols.fn_videoRaptorDetails(len(file_names), symbols.PtrPtrVideoInfo(self.array_object))

        for i in range(len(file_names)):
            video_info = self.objects[i]
            done = _info_to_params(video_info) if symbols.fn_VideoReport_isDone(pointer(video_info.report)) else None
            errors = get_video_info_errors(video_info.report)
            if done and errors:
                done['errors'] = errors
                errors = None
            output[i] = VideoRaptorResult(done=done, errors=errors)
            symbols.fn_VideoInfo_clear(self.pointers[i])

        return output


class VideoThumbnailGenerator:
    __slots__ = ('buffer_size', 'objects', 'pointers', 'array_type', 'array_object',
                 'encoded_output_folder', 'c_output_folder')

    def __init__(self, buffer_size, output_folder):
        self.buffer_size = buffer_size
        self.objects = [symbols.VideoThumbnail() for _ in range(buffer_size)]
        self.pointers = [pointer(v) for v in self.objects]
        self.array_type = symbols.PtrVideoThumbnail * buffer_size
        self.array_object = self.array_type(*self.pointers)
        self.encoded_output_folder = output_folder.encode()
        self.c_output_folder = c_char_p(self.encoded_output_folder)

    def generate(self, file_names, thumb_names):
        # type: (ListView[str], ListView[str]) -> List[VideoRaptorResult]

        assert len(file_names) == len(thumb_names) <= self.buffer_size
        output = [None] * len(file_names)  # type: List[Optional[VideoRaptorResult]]
        encoded_file_names = [file_name.encode() for file_name in file_names]
        encoded_thumb_names = [thumb_name.encode() for thumb_name in thumb_names]

        for i in range(len(file_names)):
            symbols.fn_VideoThumbnail_init(
                self.pointers[i],
                c_char_p(encoded_file_names[i]),
                self.c_output_folder,
                c_char_p(encoded_thumb_names[i])
            )

        symbols.fn_videoRaptorThumbnails(len(file_names), symbols.PtrPtrVideoThumbnail(self.array_object))

        for i in range(len(file_names)):
            video_thumb = self.objects[i]
            output[i] = VideoRaptorResult(
                done=symbols.fn_VideoReport_isDone(pointer(video_thumb.report)),
                errors=get_video_info_errors(video_thumb.report),
            )

        return output
