import sys
from ctypes import cdll, POINTER, c_char_p, c_int, c_uint, c_bool, c_double

from pysaurus.core.video_raptor.structures import VideoRaptorInfo, ErrorReader, VideoReport, VideoInfo, VideoThumbnail, c_int_p, Sequence

__PtrVideoRaptorInfo = POINTER(VideoRaptorInfo)
__PtrErrorReader = POINTER(ErrorReader)
__PtrVideoReport = POINTER(VideoReport)
__PtrVideoInfo = POINTER(VideoInfo)
__PtrVideoThumbnail = POINTER(VideoThumbnail)
__PtrPtrVideoInfo = POINTER(__PtrVideoInfo)
__PtrPtrVideoThumbnail = POINTER(__PtrVideoThumbnail)
__PtrPtrInt = POINTER(c_int_p)
__PtrSequence = POINTER(Sequence)
__PtrPtrSequence = POINTER(__PtrSequence)

if sys.platform == 'linux':
    __dll_video_raptor = cdll.LoadLibrary('videoRaptorBatch.so')
else:
    __dll_video_raptor = cdll.videoRaptorBatch
__fn_VideoRaptorInfo_init = __dll_video_raptor.VideoRaptorInfo_init
__fn_VideoRaptorInfo_clear = __dll_video_raptor.VideoRaptorInfo_clear
__fn_ErrorReader_init = __dll_video_raptor.ErrorReader_init
__fn_ErrorReader_next = __dll_video_raptor.ErrorReader_next
__fn_VideoReport_isDone = __dll_video_raptor.VideoReport_isDone
__fn_VideoReport_hasError = __dll_video_raptor.VideoReport_hasError
__fn_VideoReport_hasDeviceError = __dll_video_raptor.VideoReport_hasDeviceError
__fn_VideoInfo_init = __dll_video_raptor.VideoInfo_init
__fn_VideoInfo_clear = __dll_video_raptor.VideoInfo_clear

__fn_VideoThumbnail_init = __dll_video_raptor.VideoThumbnail_init
__fn_videoRaptorDetails = __dll_video_raptor.videoRaptorDetails
__fn_videoRaptorThumbnails = __dll_video_raptor.videoRaptorThumbnails

__fn_batchAlignmentScore = __dll_video_raptor.batchAlignmentScore
__fn_classifySimilarities = __dll_video_raptor.classifySimilarities

__fn_VideoRaptorInfo_init.argtypes = [__PtrVideoRaptorInfo]
__fn_VideoRaptorInfo_clear.argtypes = [__PtrVideoRaptorInfo]
__fn_ErrorReader_init.argtypes = [__PtrErrorReader, c_uint]
__fn_ErrorReader_next.argtypes = [__PtrErrorReader]
__fn_ErrorReader_next.restype = c_char_p
__fn_VideoReport_isDone.argtypes = [__PtrVideoReport]
__fn_VideoReport_isDone.restype = c_bool
__fn_VideoReport_hasError.argtypes = [__PtrVideoReport]
__fn_VideoReport_hasError.restype = c_bool
__fn_VideoReport_hasDeviceError.argtypes = [__PtrVideoReport]
__fn_VideoReport_hasDeviceError.restype = c_bool
__fn_VideoInfo_init.argtypes = [__PtrVideoInfo, c_char_p]
__fn_VideoInfo_clear.argtypes = [__PtrVideoInfo]
__fn_VideoThumbnail_init.argtypes = [__PtrVideoThumbnail, c_char_p, c_char_p, c_char_p]
__fn_videoRaptorDetails.argtypes = [c_int, __PtrPtrVideoInfo]
__fn_videoRaptorDetails.restype = c_int
__fn_videoRaptorThumbnails.argtypes = [c_int, __PtrPtrVideoThumbnail]
__fn_videoRaptorThumbnails.restype = c_int
__fn_batchAlignmentScore.argtypes = [c_int_p, c_int_p, c_int, c_int, c_int, c_int, c_int]
__fn_batchAlignmentScore.restype = c_double
__fn_classifySimilarities.argtypes = [__PtrPtrSequence, c_int, c_double, c_double, c_int, c_int, c_int, c_int, c_int]
__fn_classifySimilarities.restype = c_int