"""
InputContainer
    bit_rate 573785
    decode <built-in method decode of av.container.input.InputContainer object at 0x0000023584783BA8>
    demux <built-in method demux of av.container.input.InputContainer object at 0x0000023584783BA8>
    duration 84736871
    file None
    format <av.ContainerFormat 'ogg'>
    metadata {}
    name C:\donnees\programmation\git\pysaurus\pysaurus\tests\videos\Lion.ogv
    seek <built-in method seek of av.container.input.InputContainer object at 0x0000023584783BA8>
    size 6077595
    start_time 0
    streams <av.container.streams.StreamContainer object at 0x00000235847A9EB8>
    writeable False
ContainerFormat
    descriptor None
    extensions {'ogg'}
    input <av.ContainerFormat 'ogg'>
    is_input True
    is_output False
    long_name Ogg
    name ogg
    ATTRIBUTE_ERROR(options): 'NoneType' object has no attribute 'options'
    output None
StreamContainer
    audio (<av.AudioStream #1 vorbis at 44100Hz, stereo, fltp at 0x235848ad048>,)
    get <built-in method get of av.container.streams.StreamContainer object at 0x00000235847A9EB8>
    other ()
    subtitles ()
    video (<av.VideoStream #0 theora, yuv420p 532x300 at 0x235848a7638>,)
VideoStream
    average_rate 25
    bit_rate None
    bit_rate_tolerance 4000000
    buffer_size 0
    coded_height 304
    coded_width 544
    decode <built-in method decode of av.video.stream.VideoStream object at 0x00000235848A7638>
    display_aspect_ratio 0
    duration 2118
    encode <built-in method encode of av.video.stream.VideoStream object at 0x00000235848A7638>
    format <av.VideoFormat yuv420p, 532x300>
    frames 0
    gop_size 12
    has_b_frames False
    height 300
    id 0
    index 0
    language None
    long_name Theora
    max_bit_rate None
    metadata {}
    name theora
    ATTRIBUTE_ERROR(pix_fmt): attribute 'pix_fmt' of 'av.video.stream.VideoStream' objects is not readable
    profile None
    rate 1/25
    sample_aspect_ratio 0
    seek <built-in method seek of av.video.stream.VideoStream object at 0x00000235848A7638>
    start_time 0
    thread_count 1
    time_base 1/25
    type video
    width 532
AudioStream
    average_rate 0
    bit_rate 128000
    bit_rate_tolerance 4000000
    channels 2
    decode <built-in method decode of av.audio.stream.AudioStream object at 0x00000235848AD048>
    duration 3736896
    encode <built-in method encode of av.audio.stream.AudioStream object at 0x00000235848AD048>
    format <av.AudioFormat fltp>
    frame_size 0
    frames 0
    id 1
    index 1
    language None
    layout <av.AudioLayout 'stereo'>
    long_name Vorbis
    max_bit_rate None
    metadata {'ENCODER': 'Lavc52.79.1', 'TITLE': 'Wildlife video media', 'LICENSE': 'http://creativecommons.org/licenses/by-sa/3.0/', 'LOCATION': 'http://www.archive.org/details/WildlifeVideoMedia'}
    name vorbis
    profile None
    rate 44100
    seek <built-in method seek of av.audio.stream.AudioStream object at 0x00000235848AD048>
    start_time 0
    thread_count 1
    time_base 1/44100
    type audio
"""
import os

import av

from pysaurus.utils.common import PACKAGE_DIR


def debug_object(obj):
    print(obj.__class__.__name__)
    for name in sorted(dir(obj)):
        if not name.startswith('__'):
            try:
                print('    %s %s' % (name, getattr(obj, name)))
            except Exception as e:
                print('\tATTRIBUTE_ERROR(%s):' % name, e)


# video_file_path = os.path.join(PACKAGE_DIR, 'pysaurus', 'tests', 'videos', '724373406.Ogg')
video_file_path = os.path.join(PACKAGE_DIR, 'pysaurus', 'tests', 'videos', 'Lion.ogv')
container = av.open(video_file_path)
debug_object(container)
debug_object(container.format)
debug_object(container.streams)
if container.streams.video:
    first_video_stream = container.streams.video[0]
    debug_object(first_video_stream)
if container.streams.audio:
    first_audio_stream = container.streams.audio[0]
    debug_object(first_audio_stream)
