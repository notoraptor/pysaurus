from ctypes import cdll, POINTER, c_bool, c_int, c_char_p, c_void_p, pointer
from pyraptor.c_video import CVideo
from pyraptor.video import Video

__NB_READS = 200
__StringArray = c_char_p * __NB_READS
__CVideoPtrArr = POINTER(CVideo) * __NB_READS

__dll_video_raptor = cdll.videoRaptorBatch
__fn_create_output = __dll_video_raptor.createOutput
__fn_output_to_string = __dll_video_raptor.outputToString
__fn_delete_output = __dll_video_raptor.deleteOutput
__fn_flush_logger = __dll_video_raptor.flushLogger
__fn_video_raptor_details = __dll_video_raptor.videoRaptorDetails

__fn_create_output.restype = c_void_p
__fn_output_to_string.argtypes = [c_void_p]
__fn_output_to_string.restype = c_char_p
__fn_delete_output.argtypes = [c_void_p]
__fn_flush_logger.restype = c_char_p
__fn_video_raptor_details.argtypes = [c_int, __StringArray, __CVideoPtrArr, c_void_p]
__fn_video_raptor_details.restype = c_bool


def get_n_reads():
    return __NB_READS


def get_video_details(file_names):
    if len(file_names) > __NB_READS:
        raise Exception('Expected at most %d filenames, got %d' % (__NB_READS, len(file_names)))
    if len(file_names) < __NB_READS:
        file_names = list(file_names) + ([None] * (__NB_READS - len(file_names)))
    ascii_file_names = [filename.encode() if filename else None for filename in file_names]
    c_video_array = [CVideo() if filename else None for filename in file_names]
    c_video_pointers = [pointer(c_video) if c_video else None for c_video in c_video_array]
    output = __fn_create_output()
    res = __fn_video_raptor_details(
        __NB_READS, __StringArray(*ascii_file_names), __CVideoPtrArr(*c_video_pointers), output)
    messages = __fn_output_to_string(output)
    __fn_delete_output(output)
    videos = [Video(c_video) if c_video else None for c_video in c_video_array]
    return res, messages.decode(), videos


def pop_logger():
    return __fn_flush_logger().decode()
