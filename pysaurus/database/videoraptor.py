from ctypes import *

VIDEO_BATCH_SIZE = 4
c_arr_t = c_char_p * VIDEO_BATCH_SIZE

video_raptor_dll = cdll.videoRaptorBatch
create_output = video_raptor_dll.createOutput
output_to_string = video_raptor_dll.outputToString
delete_output = video_raptor_dll.deleteOutput
video_raptor = video_raptor_dll.videoRaptorBatch

create_output.restype = c_void_p
video_raptor.argtypes = [c_int, c_arr_t, c_arr_t, c_char_p, c_void_p]
output_to_string.argtypes = [c_void_p]
output_to_string.restype = c_char_p
delete_output.argtypes = [c_void_p]

DEFAULT_THUMB_ARG = c_arr_t(*([None] * VIDEO_BATCH_SIZE))

def run(file_names, start, thumb_folder=None, thumb_id_start=None):
    real_len = min(len(file_names) - start, VIDEO_BATCH_SIZE)
    if real_len <= 0:
        return None
    c_file_names = ([file_name.encode() for file_name in file_names[start:(start + real_len)]]
                    + ([None] * (VIDEO_BATCH_SIZE - real_len)))

    output = create_output()
    video_raptor(
        VIDEO_BATCH_SIZE,
        c_arr_t(*c_file_names),
        c_arr_t(*[str(thumb_id_start + i).encode() for i in range(real_len)]) if thumb_folder else DEFAULT_THUMB_ARG,
        thumb_folder.encode() if thumb_folder else None,
        output)
    result = output_to_string(output)
    delete_output(output)
    return result.decode(), real_len
