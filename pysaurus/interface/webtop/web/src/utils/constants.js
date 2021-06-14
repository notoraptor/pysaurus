export const HomeStatus = {
    INITIAL: 0,
    LOADING: 1,
    LOADED: 2
}

export const GroupPermission = {
    FORBIDDEN: 0,
    ONLY_MANY: 1,
    ALL: 2
};

class FieldInfo {
    /**
     * @param name {string}
     * @param title {string}
     * @param groupPermission {number}
     * @param isString {boolean}
     */
    constructor(name, title, groupPermission, isString) {
        this.name = name;
        this.title = title ? title : name.replace(/_/g, " ");
        this.groupPermission = groupPermission;
        this.isString = isString;
    }

    isForbidden() {
        return this.groupPermission === GroupPermission.FORBIDDEN;
    }

    isOnlyMany() {
        return this.groupPermission === GroupPermission.ONLY_MANY;
    }

    isAll() {
        return this.groupPermission === GroupPermission.ALL;
    }
}

class FieldMap {
    /**
     * @param fieldInfoList {Array.<FieldInfo>}
     */
    constructor(fieldInfoList) {
        this.list = fieldInfoList;
        this.fields = {};
        for (let fieldInfo of fieldInfoList) {
            if (this.fields.hasOwnProperty(fieldInfo.name))
                throw new Error(`Duplicated field: ${fieldInfo.name}`);
            this.fields[fieldInfo.name] = fieldInfo;
        }
        this.list.sort((f1, f2) => (
                f1.title.localeCompare(f2.title) || f1.name.localeCompare(f2.name)
            )
        );
    }
}

export const FIELD_MAP = new FieldMap([
    new FieldInfo('audio_bit_rate', '', GroupPermission.ALL, false),
    new FieldInfo('audio_codec', '', GroupPermission.ALL, true),
    new FieldInfo('audio_codec_description', '', GroupPermission.ALL, true),
    new FieldInfo('bit_depth', '', GroupPermission.ALL, false),
    new FieldInfo('container_format', '', GroupPermission.ALL, true),
    new FieldInfo('date', 'date modified', GroupPermission.FORBIDDEN, true),
    new FieldInfo('day', '', GroupPermission.ALL, true),
    new FieldInfo('disk', '', GroupPermission.ALL, true),
    new FieldInfo('extension', 'file extension', GroupPermission.ALL, true),
    new FieldInfo('file_size', 'file size (bytes)', GroupPermission.ONLY_MANY, true),
    new FieldInfo('file_title', '', GroupPermission.ONLY_MANY, true),
    new FieldInfo('filename', 'file path', GroupPermission.ONLY_MANY, true),
    new FieldInfo('frame_rate', '', GroupPermission.ALL, false),
    new FieldInfo('height', '', GroupPermission.ALL, false),
    new FieldInfo('length', '', GroupPermission.ONLY_MANY, false),
    new FieldInfo('properties', '', GroupPermission.FORBIDDEN, false),
    new FieldInfo('quality', '', GroupPermission.FORBIDDEN, false),
    new FieldInfo('sample_rate', '', GroupPermission.ALL, false),
    new FieldInfo('size', '', GroupPermission.ONLY_MANY, false),
    new FieldInfo('thumbnail_path', '', GroupPermission.FORBIDDEN, true),
    new FieldInfo('title', '', GroupPermission.ONLY_MANY, true),
    new FieldInfo('video_codec', '', GroupPermission.ALL, true),
    new FieldInfo('video_codec_description', '', GroupPermission.ALL, true),
    new FieldInfo('video_id', 'video ID', GroupPermission.FORBIDDEN, false),
    new FieldInfo('width', '', GroupPermission.ALL, false),
]);

export const SEARCH_TYPE_TITLE = {
    exact: 'exactly',
    and: 'all terms',
    or: 'any term'
};

export const PAGE_SIZES = [10, 20, 50, 100];

export const VIDEO_DEFAULT_PAGE_SIZE = PAGE_SIZES[PAGE_SIZES.length - 1];

export const VIDEO_DEFAULT_PAGE_NUMBER = 0;

export const SOURCE_TREE = {
    // unreadable: {not_found: false, found: false},
    readable: {
        not_found: {with_thumbnails: false, without_thumbnails: false},
        found: {with_thumbnails: false, without_thumbnails: false},
    },
};

export const Characters = {
    CROSS: "\u2715",
    SETTINGS: "\u2630",
    ARROW_DOWN: "\u25BC",
    ARROW_UP: "\u25B2",
    SMART_ARROW_LEFT: "\u2B9C",
    SMART_ARROW_RIGHT: "\u2B9E",
}
