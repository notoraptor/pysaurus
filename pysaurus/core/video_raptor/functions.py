import sys
from ctypes import POINTER, c_bool, c_char_p, c_double, c_int, c_uint, cdll

from pysaurus.core.video_raptor.structures import (ErrorReader, Sequence, VideoInfo, VideoRaptorInfo, VideoReport,
                                                   VideoThumbnail, c_int_p)

c_double_p = POINTER(c_double)
PtrVideoRaptorInfo = POINTER(VideoRaptorInfo)
PtrErrorReader = POINTER(ErrorReader)
PtrVideoReport = POINTER(VideoReport)
PtrVideoInfo = POINTER(VideoInfo)
PtrVideoThumbnail = POINTER(VideoThumbnail)
PtrPtrVideoInfo = POINTER(PtrVideoInfo)
PtrPtrVideoThumbnail = POINTER(PtrVideoThumbnail)
PtrPtrInt = POINTER(c_int_p)
PtrSequence = POINTER(Sequence)
PtrPtrSequence = POINTER(PtrSequence)

if sys.platform == 'linux':
    __dll_video_raptor = cdll.LoadLibrary('videoRaptorBatch.so')
else:
    __dll_video_raptor = cdll.videoRaptorBatch
fn_VideoRaptorInfo_init = __dll_video_raptor.VideoRaptorInfo_init
fn_VideoRaptorInfo_clear = __dll_video_raptor.VideoRaptorInfo_clear
fn_ErrorReader_init = __dll_video_raptor.ErrorReader_init
fn_ErrorReader_next = __dll_video_raptor.ErrorReader_next
fn_VideoReport_isDone = __dll_video_raptor.VideoReport_isDone
fn_VideoReport_hasError = __dll_video_raptor.VideoReport_hasError
fn_VideoReport_hasDeviceError = __dll_video_raptor.VideoReport_hasDeviceError
fn_VideoInfo_init = __dll_video_raptor.VideoInfo_init
fn_VideoInfo_clear = __dll_video_raptor.VideoInfo_clear

fn_VideoThumbnail_init = __dll_video_raptor.VideoThumbnail_init
fn_videoRaptorDetails = __dll_video_raptor.videoRaptorDetails
fn_videoRaptorThumbnails = __dll_video_raptor.videoRaptorThumbnails

fn_batchAlignmentScore = __dll_video_raptor.batchAlignmentScore
fn_classifySimilarities = __dll_video_raptor.classifySimilarities

fn_VideoRaptorInfo_init.argtypes = [PtrVideoRaptorInfo]
fn_VideoRaptorInfo_clear.argtypes = [PtrVideoRaptorInfo]
fn_ErrorReader_init.argtypes = [PtrErrorReader, c_uint]
fn_ErrorReader_next.argtypes = [PtrErrorReader]
fn_ErrorReader_next.restype = c_char_p
fn_VideoReport_isDone.argtypes = [PtrVideoReport]
fn_VideoReport_isDone.restype = c_bool
fn_VideoReport_hasError.argtypes = [PtrVideoReport]
fn_VideoReport_hasError.restype = c_bool
fn_VideoReport_hasDeviceError.argtypes = [PtrVideoReport]
fn_VideoReport_hasDeviceError.restype = c_bool
fn_VideoInfo_init.argtypes = [PtrVideoInfo, c_char_p]
fn_VideoInfo_clear.argtypes = [PtrVideoInfo]
fn_VideoThumbnail_init.argtypes = [PtrVideoThumbnail, c_char_p, c_char_p, c_char_p]
fn_videoRaptorDetails.argtypes = [c_int, PtrPtrVideoInfo]
fn_videoRaptorDetails.restype = c_int
fn_videoRaptorThumbnails.argtypes = [c_int, PtrPtrVideoThumbnail]
fn_videoRaptorThumbnails.restype = c_int
fn_batchAlignmentScore.argtypes = [c_int_p, c_int_p, c_int, c_int, c_int, c_int, c_int]
fn_batchAlignmentScore.restype = c_double
fn_classifySimilarities.argtypes = [PtrPtrSequence, c_int, c_int, c_int, c_double_p]
