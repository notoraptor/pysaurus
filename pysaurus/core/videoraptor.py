from ctypes import cdll, POINTER, c_int, c_char_p, c_void_p, pointer

from pysaurus.core.c_video import CVideo
from pysaurus.core.video import Video

__NB_READS = 200
__StrArr = c_char_p * __NB_READS
__CVideoPtrArr = POINTER(CVideo) * __NB_READS

__dll_video_raptor = cdll.videoRaptorBatch
__fn_create_output = __dll_video_raptor.createOutput
__fn_output_to_string = __dll_video_raptor.outputToString
__fn_delete_output = __dll_video_raptor.deleteOutput
__fn_video_raptor_details = __dll_video_raptor.videoRaptorDetails
__fn_video_raptor_thumbnails = __dll_video_raptor.videoRaptorThumbnails

__fn_create_output.restype = c_void_p
__fn_output_to_string.argtypes = [c_void_p]
__fn_output_to_string.restype = c_char_p
__fn_delete_output.argtypes = [c_void_p]
__fn_video_raptor_details.argtypes = [c_int, __StrArr, __CVideoPtrArr, c_void_p]
__fn_video_raptor_details.restype = c_int
__fn_video_raptor_thumbnails.argtypes = [c_int, __StrArr, __StrArr, c_char_p, c_void_p]
__fn_video_raptor_thumbnails.restype = c_int


def get_n_reads():
    return __NB_READS


def get_video_details(file_names):
    if len(file_names) > __NB_READS:
        raise Exception('Expected at most %d filenames, got %d' % (__NB_READS, len(file_names)))
    missing_n_reads = __NB_READS - len(file_names)
    c_video_array = [CVideo() for _ in file_names]
    c_video_pointers = [pointer(c_video) for c_video in c_video_array] + ([None] * missing_n_reads)
    ascii_file_names = [filename.encode() for filename in file_names] + ([None] * missing_n_reads)
    output = __fn_create_output()
    res = __fn_video_raptor_details(__NB_READS, __StrArr(*ascii_file_names), __CVideoPtrArr(*c_video_pointers), output)
    messages = __fn_output_to_string(output)
    __fn_delete_output(output)
    videos = [Video(c_video) for c_video in c_video_array]
    return res, messages.decode(), videos


def generate_thumbnails(file_names, thumb_names, thumb_folder):
    if len(file_names) > __NB_READS:
        raise Exception('Expected at most %d file names, got %d.' % (__NB_READS, len(file_names)))
    missing_n_reads = __NB_READS - len(file_names)
    ascii_file_names = [file_name.encode() for file_name in file_names] + ([None] * missing_n_reads)
    ascii_thumb_names = [thumb_name.encode() if thumb_name else None for thumb_name in thumb_names] + (
            [None] * missing_n_reads)
    ascii_thumb_folder = thumb_folder.encode()
    output = __fn_create_output()
    res = __fn_video_raptor_thumbnails(__NB_READS, __StrArr(*ascii_file_names), __StrArr(*ascii_thumb_names),
                                       ascii_thumb_folder, output)
    messages = __fn_output_to_string(output)
    __fn_delete_output(output)
    return res, messages.decode()
