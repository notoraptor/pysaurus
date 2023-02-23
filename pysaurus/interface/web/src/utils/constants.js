import { tr } from "../language.js";

export const GroupPermission = {
	FORBIDDEN: 0,
	ONLY_MANY: 1,
	ALL: 2,
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
	 */
	constructor(fieldInfoList) {
		this.list = fieldInfoList;
		this.allowed = [];
		this.sortable = [];
		this.fields = {};
		for (let fieldInfo of fieldInfoList) {
			if (this.fields.hasOwnProperty(fieldInfo.name))
				throw new Error(
					tr("Duplicated field: {name}", {
						name: fieldInfo.name,
					})
				);
			this.fields[fieldInfo.name] = fieldInfo;
			if (!fieldInfo.isForbidden()) this.allowed.push(fieldInfo);
			if (fieldInfo.isSortable()) this.sortable.push(fieldInfo);
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

export const FIELD_MAP = new FieldMap([
	new FieldInfo("audio_bit_rate", tr("audio bit rate"), GroupPermission.ALL, FieldType.int),
	new FieldInfo("audio_codec", tr("audio codec"), GroupPermission.ALL, FieldType.str),
	new FieldInfo("audio_codec_description", tr("audio codec description"), GroupPermission.ALL, FieldType.str),
	new FieldInfo("bit_depth", tr("bit depth"), GroupPermission.ALL, FieldType.int),
	new FieldInfo("container_format", tr("container format"), GroupPermission.ALL, FieldType.str),
	new FieldInfo("date", tr("date modified"), GroupPermission.ONLY_MANY, FieldType.sortable),
	new FieldInfo("date_entry_modified", tr("date entry modified"), GroupPermission.ONLY_MANY, FieldType.sortable),
	new FieldInfo("day", tr("day"), GroupPermission.ALL, FieldType.str),
	new FieldInfo("disk", tr("disk"), GroupPermission.ALL, FieldType.str),
	new FieldInfo("extension", tr("file extension"), GroupPermission.ALL, FieldType.str),
	new FieldInfo("file_size", tr("file size (bytes)"), GroupPermission.ONLY_MANY, FieldType.int),
	new FieldInfo("file_title", tr("file title"), GroupPermission.ONLY_MANY, FieldType.str),
	new FieldInfo("file_title_numeric", tr("file title (with numbers)"), GroupPermission.ONLY_MANY, FieldType.sortable),
	new FieldInfo("filename", tr("file path"), GroupPermission.ONLY_MANY, FieldType.str),
	new FieldInfo("filename_numeric", tr("file path (with numbers)"), GroupPermission.ONLY_MANY, FieldType.sortable),
	new FieldInfo("frame_rate", tr("frame rate"), GroupPermission.ALL, FieldType.float),
	new FieldInfo("height", tr("height"), GroupPermission.ALL, FieldType.int),
	new FieldInfo("length", tr("length"), GroupPermission.ONLY_MANY, FieldType.sortable),
	new FieldInfo("move_id", tr("moved files (potentially)"), GroupPermission.ONLY_MANY, FieldType.unsortable),
	new FieldInfo("properties", tr("properties"), GroupPermission.FORBIDDEN, FieldType.unsortable),
	new FieldInfo("quality", tr("quality"), GroupPermission.ONLY_MANY, FieldType.float),
	new FieldInfo("sample_rate", tr("sample rate"), GroupPermission.ALL, FieldType.int),
	new FieldInfo("similarity_id", tr("similarity"), GroupPermission.ONLY_MANY, FieldType.unsortable),
	new FieldInfo("size", tr("size"), GroupPermission.ONLY_MANY, FieldType.sortable),
	new FieldInfo("thumbnail_path", tr("thumbnail path"), GroupPermission.FORBIDDEN, FieldType.unsortable),
	new FieldInfo("title", tr("title"), GroupPermission.ONLY_MANY, FieldType.str),
	new FieldInfo("title_numeric", tr("title (with numbers)"), GroupPermission.ONLY_MANY, FieldType.sortable),
	new FieldInfo("video_codec", tr("video codec"), GroupPermission.ALL, FieldType.str),
	new FieldInfo("video_codec_description", tr("video codec description"), GroupPermission.ALL, FieldType.str),
	new FieldInfo("video_id", tr("video ID"), GroupPermission.FORBIDDEN, FieldType.int),
	new FieldInfo("width", tr("width"), GroupPermission.ALL, FieldType.int),
	new FieldInfo("size_length", "(size and length)", GroupPermission.ONLY_MANY, FieldType.sortable),
]);

export const PAGE_SIZES = [1, 10, 20, 50, 100];

export const VIDEO_DEFAULT_PAGE_SIZE = PAGE_SIZES[PAGE_SIZES.length - 1];

export const VIDEO_DEFAULT_PAGE_NUMBER = 0;

export const SOURCE_TREE = {
	unreadable: { not_found: false, found: false },
	readable: {
		not_found: { with_thumbnails: false, without_thumbnails: false },
		found: { with_thumbnails: false, without_thumbnails: false },
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
};

export const SearchTypeTitle = {
	exact: tr("exactly"),
	and: tr("all terms"),
	or: tr("any term"),
	id: tr("video ID"),
};
