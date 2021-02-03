export const HomeStatus = {
    INITIAL: 0,
    LOADING: 1,
    LOADED: 2
}

export const GroupPermission = {
    FORBIDDEN: 0,
    ONLY_ONE: 1,
    ONLY_MANY: 2,
    ALL: 3
};

export const FIELDS_GROUP_DEF = {
    'audio_bit_rate': GroupPermission.ALL,
    'audio_codec': GroupPermission.ALL,
    'audio_codec_description': GroupPermission.ALL,
    'container_format': GroupPermission.ALL,
    'date': GroupPermission.FORBIDDEN,
    'day': GroupPermission.ALL,
    'disk': GroupPermission.ALL,
    'extension': GroupPermission.ALL,
    'file_size': GroupPermission.ONLY_MANY,
    'file_title': GroupPermission.ONLY_MANY,
    'filename': GroupPermission.ONLY_MANY,
    'frame_rate': GroupPermission.ALL,
    'height': GroupPermission.ALL,
    'length': GroupPermission.ONLY_MANY,
    'properties': GroupPermission.FORBIDDEN,
    'quality': GroupPermission.FORBIDDEN,
    'sample_rate': GroupPermission.ALL,
    'size': GroupPermission.ONLY_MANY,
    'thumbnail_path': GroupPermission.FORBIDDEN,
    'title': GroupPermission.ONLY_MANY,
    'video_codec': GroupPermission.ALL,
    'video_codec_description': GroupPermission.ALL,
    'video_id': GroupPermission.FORBIDDEN,
    'width': GroupPermission.ALL,
};

export const STRING_FIELDS = {
    'audio_codec': true,
    'audio_codec_description': true,
    'container_format': true,
    'day': true,
    'disk': true,
    'extension': true,
    'file_size': true,
    'file_title': true,
    'filename': true,
    'thumbnail_path': true,
    'title': true,
    'video_codec': true,
    'video_codec_description': true,
};

export const FIELD_TITLES = {
    'audio_bit_rate': 'audio bit rate',
    'audio_codec': 'audio codec',
    'audio_codec_description': 'audio codec description',
    'container_format': 'container format',
    'date' : 'date modified',
    'day' : 'day',
    'disk' : 'disk',
    'extension': 'file extension',
    'file_size': 'size (bytes)',
    'file_title': 'file title',
    'filename': 'file path',
    'frame_rate': 'frame rate',
    'height': 'height',
    'length': 'length',
    'properties': 'properties',
    'quality': 'quality',
    'sample_rate' : 'sample rate',
    'size': 'size',
    'thumbnail_path': 'thumbnail path',
    'title': 'title',
    'video_codec': 'video codec',
    'video_codec_description' : 'video codec description',
    'video_id': 'video ID',
    'width': 'width',
};

export const SORTED_FIELDS_AND_TITLES = (function (obj) {
    const arr = Object.keys(obj).map(key => [key, obj[key]]);
    arr.sort(function(t1, t2) {
        let t = t1[1].localeCompare(t2[1]);
        if (t === 0)
            t = t1[0].localeCompare(t2[0]);
        return t;
    });
    return arr;
})(FIELD_TITLES);

export const SEARCH_TYPE_TITLE = {
    exact: 'exactly',
    and: 'all terms',
    or: 'any term'
};

export const PAGE_SIZES = [10, 20, 50, 100];

export const VIDEO_DEFAULT_PAGE_SIZE = PAGE_SIZES[PAGE_SIZES.length - 1];

export const VIDEO_DEFAULT_PAGE_NUMBER = 0;
