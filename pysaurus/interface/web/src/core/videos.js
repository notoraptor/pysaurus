export const Fields = {
	filename: 'filename',
	container_format: 'container_format',
	audio_codec: 'audio_codec',
	video_codec: 'video_codec',
	width: 'width',
	height: 'height',
	sample_rate: 'sample_rate',
	audio_bit_rate: 'audio_bit_rate',
	errors: 'errors',
	frame_rate: 'frame_rate',
	duration_string: 'duration_string',
	duration_value: 'duration_value',
	size_string: 'size_string',
	size_value: 'size_value',
	date_string: 'date_string',
	date_value: 'date_value',
	meta_title: 'meta_title',
	file_title: 'file_title',
	extension: 'extension'
};

export const Extra = {
	image64: 'image64',
	clip: 'clip',
	clipIsLoading: 'clipIsLoading',
};

export class VideoClip {
	constructor(index, length, url) {
		this.index = index;
		this.length = length;
		this.url = url;
	}
}

export class Videos {
	constructor(table) {
		/** @var Array table */
		this.headers = table.shift();
		this.lines = table;
		this.extras = {};
		this.fieldIndex = {};
		for (let i = 0; i < this.headers.length; ++i) {
			this.fieldIndex[this.headers[i]] = i;
		}
		this.sortField = null;
		this.sortReverse = false;
	}

	size() {
		return this.lines.length;
	}

	sort(field, reverse) {
		reverse = !!reverse;
		if (this.sortField === field && this.sortReverse === reverse)
			return;
		this.lines.sort((a, b) => {
			const valueA = this.getFromLine(a, field);
			const valueB = this.getFromLine(b, field);
			if (valueA < valueB)
				return -1;
			if (valueA > valueB)
				return 1;
			return 0;
		});
		this.sortField = field;
		this.sortReverse = reverse;
	}

	get(index, field) {
		if (field === 'name')
			return this.getName(index);
		return this.lines[index][this.fieldIndex[field]];
	}

	getName(index) {
		const metaTitle = this.get(index, Fields.meta_title);
		return metaTitle ? metaTitle : this.get(index, Fields.file_title);
	}

	getNameFromLine(line) {
		const metaTitle = line[this.fieldIndex[Fields.meta_title]];
		return metaTitle ? metaTitle : line[this.fieldIndex[Fields.file_title]];
	}

	getFromLine(line, field) {
		if (field === 'name')
			return this.getNameFromLine(line);
		return line[this.fieldIndex[field]];
	}

	setExtra(index, field, value) {
		const filename = this.get(index, Fields.filename);
		if (!this.extras.hasOwnProperty(filename))
			this.extras[filename] = {};
		this.extras[filename][field] = value;
	}

	getExtra(index, field) {
		const filename = this.get(index, Fields.filename);
		if (this.extras.hasOwnProperty(filename)) {
			const extra = this.extras[filename];
			if (extra.hasOwnProperty(field))
				return extra[field];
		}
		return null;
	}

	getPrintableVideo(index) {
		const video = {};
		for (let field of [
			Fields.filename,
			Fields.container_format,
			Fields.audio_codec,
			Fields.video_codec,
			Fields.width,
			Fields.height,
			Fields.sample_rate,
			Fields.audio_bit_rate,
			Fields.frame_rate,
			Fields.duration_string,
			Fields.size_string,
			Fields.date_string,
			Fields.extension,
		]) {
			video[field] = this.get(index, field);
		}
		video.frame_rate = Math.round(video.frame_rate);
		video.name = this.getName(index);
		video.index = index;
		return video;
	}
}
