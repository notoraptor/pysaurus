import os
from _ctypes import pointer
from ctypes import c_char_p

from pysaurus.core.thumbnail_utils import VideoThumbnailResult
from pysaurus.core.video import Video
from pysaurus.core.video_raptor.functions import (__fn_VideoRaptorInfo_init, __fn_VideoRaptorInfo_clear,
                                                  __fn_VideoReport_hasError, __fn_ErrorReader_init,
                                                  __fn_ErrorReader_next, __PtrVideoInfo, __fn_VideoInfo_init,
                                                  __fn_videoRaptorDetails, __PtrPtrVideoInfo, __fn_VideoReport_isDone,
                                                  __fn_VideoInfo_clear, __PtrVideoThumbnail,
                                                  __fn_VideoThumbnail_init, __fn_videoRaptorThumbnails,
                                                  __PtrPtrVideoThumbnail)
from pysaurus.core.video_raptor.structures import VideoRaptorInfo, ErrorReader, VideoInfo, VideoThumbnail


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


def collect_video_info(filename_dictionary: dict):
    if not filename_dictionary:
        return

    file_names = [os.path.abspath(file_name) for file_name in filename_dictionary.keys()]
    encoded_file_names = [file_name.encode() for file_name in file_names]
    video_info_objects = [VideoInfo() for _ in file_names]
    video_info_pointers = [pointer(v) for v in video_info_objects]
    array_type = __PtrVideoInfo * len(file_names)
    array_object = array_type(*video_info_pointers)

    for i in range(len(file_names)):
        __fn_VideoInfo_init(video_info_pointers[i], c_char_p(encoded_file_names[i]))

    __fn_videoRaptorDetails(len(file_names), __PtrPtrVideoInfo(array_object))

    for i in range(len(file_names)):
        filename = file_names[i]
        video_info = video_info_objects[i]
        errors = get_video_info_errors(video_info.report)
        if __fn_VideoReport_isDone(pointer(video_info.report)):
            video = Video(video_info)
            video.errors = set(errors)
            filename_dictionary[filename] = video
        elif errors:
            filename_dictionary[filename] = errors
        __fn_VideoInfo_clear(video_info_pointers[i])


def generate_video_thumbnails(file_name_to_thumb_name: dict, output_folder: str):
    if not file_name_to_thumb_name:
        return

    file_names = []
    thumb_names = []
    for (file_name, thumb_name) in file_name_to_thumb_name.items():
        file_names.append(file_name)
        thumb_names.append(thumb_name)
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
        file_name_to_thumb_name[file_names[i]] = VideoThumbnailResult(
            done=__fn_VideoReport_isDone(pointer(video_thumb.report)),
            errors=get_video_info_errors(video_thumb.report),
        )
