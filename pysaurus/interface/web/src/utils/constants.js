export const GroupPermission = {
    FORBIDDEN: 0,
    ONLY_MANY: 1,
    ALL: 2
};

const FieldType = {
    bool: 0,
    int: 1,
    float: 2,
    str: 3,
    sortable: 4,
    unsortable: 5,
};

class FieldInfo {
    /**
     * @param name {string}
     * @param title {string}
     * @param groupPermission {number}
     * @param fieldType {number}
     */
    constructor(name, title, groupPermission, fieldType) {
        this.name = name;
        this.title = title ? title : name.replace(/_/g, " ");
        this.groupPermission = groupPermission;
        this.fieldType = fieldType;
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

    isString() {
        return this.fieldType === FieldType.str;
    }

    isSortable() {
        return this.fieldType !== FieldType.unsortable;
    }
}

class FieldMap {
    /**
     * @param fieldInfoList {Array.<FieldInfo>}
     * @param context {Object}
     */
    constructor(fieldInfoList, context) {
        this.list = fieldInfoList;
        this.allowed = [];
        this.sortable = [];
        this.fields = {};
        for (let fieldInfo of fieldInfoList) {
            if (this.fields.hasOwnProperty(fieldInfo.name))
                throw new Error(context.error_duplicated_field.format({name: fieldInfo.name}));
            this.fields[fieldInfo.name] = fieldInfo;
            if (!fieldInfo.isForbidden()) {
                this.allowed.push(fieldInfo);
                if (fieldInfo.isSortable())
                    this.sortable.push(fieldInfo);
            }
        }
        this.list.sort(FieldMap.compareFieldInfo);
        this.allowed.sort(FieldMap.compareFieldInfo);
    }

    /**
     * Comparison method for FieldInfo class.
     * @param f1 {FieldInfo}
     * @param f2 {FieldInfo}
     * @returns {number}
     */
    static compareFieldInfo(f1, f2) {
        return f1.title.localeCompare(f2.title) || f1.name.localeCompare(f2.name);
    }
}

export function getFieldMap(context) {
    return new FieldMap([
        new FieldInfo('audio_bit_rate', context.attr_audio_bit_rate, GroupPermission.ALL, FieldType.int),
        new FieldInfo('audio_codec', context.attr_audio_codec, GroupPermission.ALL, FieldType.str),
        new FieldInfo('audio_codec_description', context.attr_audio_codec_description, GroupPermission.ALL, FieldType.str),
        new FieldInfo('bit_depth', context.attr_bit_depth, GroupPermission.ALL, FieldType.int),
        new FieldInfo('container_format', context.attr_container_format, GroupPermission.ALL, FieldType.str),
        new FieldInfo('date', context.attr_date, GroupPermission.ONLY_MANY, FieldType.sortable),
        new FieldInfo('day', context.attr_day, GroupPermission.ALL, FieldType.str),
        new FieldInfo('disk', context.attr_disk, GroupPermission.ALL, FieldType.str),
        new FieldInfo('extension', context.attr_extension, GroupPermission.ALL, FieldType.str),
        new FieldInfo('file_size', context.attr_file_size, GroupPermission.ONLY_MANY, FieldType.int),
        new FieldInfo('file_title', context.attr_file_title, GroupPermission.ONLY_MANY, FieldType.str),
        new FieldInfo('file_title_numeric', context.attr_file_title_numeric, GroupPermission.ONLY_MANY, FieldType.sortable),
        new FieldInfo('filename', context.attr_filename, GroupPermission.ONLY_MANY, FieldType.str),
        new FieldInfo('filename_numeric', context.attr_filename_numeric, GroupPermission.ONLY_MANY, FieldType.sortable),
        new FieldInfo('frame_rate', context.attr_frame_rate, GroupPermission.ALL, FieldType.float),
        new FieldInfo('height', context.attr_height, GroupPermission.ALL, FieldType.int),
        new FieldInfo('length', context.attr_length, GroupPermission.ONLY_MANY, FieldType.sortable),
        new FieldInfo('move_id', context.attr_move_id, GroupPermission.ONLY_MANY, FieldType.unsortable),
        new FieldInfo('properties', context.attr_properties, GroupPermission.FORBIDDEN, FieldType.unsortable),
        new FieldInfo('quality', context.attr_quality, GroupPermission.ONLY_MANY, FieldType.float),
        new FieldInfo('sample_rate', context.attr_sample_rate, GroupPermission.ALL, FieldType.int),
        new FieldInfo('similarity_id', context.attr_similarity_id, GroupPermission.ONLY_MANY, FieldType.unsortable),
        new FieldInfo('size', context.attr_size, GroupPermission.ONLY_MANY, FieldType.sortable),
        new FieldInfo('thumbnail_path', context.attr_thumbnail_path, GroupPermission.FORBIDDEN, FieldType.str),
        new FieldInfo('title', context.attr_title, GroupPermission.ONLY_MANY, FieldType.str),
        new FieldInfo('title_numeric', context.attr_title_numeric, GroupPermission.ONLY_MANY, FieldType.sortable),
        new FieldInfo('video_codec', context.attr_video_codec, GroupPermission.ALL, FieldType.str),
        new FieldInfo('video_codec_description', context.attr_video_codec_description, GroupPermission.ALL, FieldType.str),
        new FieldInfo('video_id', context.attr_video_id, GroupPermission.FORBIDDEN, FieldType.int),
        new FieldInfo('width', context.attr_width, GroupPermission.ALL, FieldType.int),
    ], context);
}

export const PAGE_SIZES = [1, 10, 20, 50, 100];

export const VIDEO_DEFAULT_PAGE_SIZE = PAGE_SIZES[PAGE_SIZES.length - 1];

export const VIDEO_DEFAULT_PAGE_NUMBER = 0;

export const SOURCE_TREE = {
    unreadable: {not_found: false, found: false},
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
    WARNING_SIGN: "\u26A0", // ⚠
}
