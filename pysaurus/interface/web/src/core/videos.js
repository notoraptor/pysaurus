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

export const Sort = {
	filename: 'path',
	container_format: 'format',
	audio_codec: 'audio codec',
	video_codec: 'video codec',
	width: 'width',
	height: 'height',
	sample_rate: 'sample rate',
	audio_bit_rate: 'audio bit rate',
	frame_rate: 'frame rate',
	duration_value: 'duration',
	size_value: 'size',
	date_value: 'date',
	meta_title: 'title (meta tag)',
	file_title: 'title (file name)',
	extension: 'extension',
	name: 'title',
	quality: 'quality'
};

export const Extra = {
	image64: 'image64',
	newName: 'newName'
};

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
		this.get = this.get.bind(this);
		this.getFromLine = this.getFromLine.bind(this);
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
			let ret = 0;
			if (valueA < valueB)
				ret = -1;
			else if (valueA > valueB)
				ret = 1;
			return reverse ? -ret : ret;
		});
		this.sortField = field;
		this.sortReverse = reverse;
	}

	remove(index) {
		if (index >= 0 && index < this.lines.length) {
			const filename = this.get(index, Fields.filename);
			if (this.extras.hasOwnProperty(filename))
				delete this.extras[filename];
			this.lines.splice(index, 1);
		}
	}

	changeFilename(index, newFilename, newFileTitle) {
		if (index >= 0 && index < this.lines.length) {
			const filename = this.get(index, Fields.filename);
			let extra = null;
			if (this.extras.hasOwnProperty(filename)) {
				extra = this.extras[filename];
				delete this.extras[filename];
				if (extra.hasOwnProperty(Extra.newName))
					delete extra.newName;
			}
			this.lines[index][this.fieldIndex[Fields.filename]] = newFilename;
			this.lines[index][this.fieldIndex[Fields.file_title]] = newFileTitle;
			if (extra)
				this.extras[newFilename] = extra;
		}
	}

	get(index, field) {
		if (field === 'name')
			return this.getName(index);
		if (field === 'quality')
			return this.getQuality(index);
		return this.lines[index][this.fieldIndex[field]];
	}

	getFromLine(line, field) {
		if (field === 'name')
			return this.getNameFromLine(line);
		if (field === 'quality')
			return this.getQualityFromLine(line);
		return line[this.fieldIndex[field]];
	}

	getName(index) {
		const metaTitle = this.get(index, Fields.meta_title);
		return metaTitle ? metaTitle : this.get(index, Fields.file_title);
	}

	static computeQuality(data, getter) {
		// !!audio_codec, width, height, !errors.length, frame_rate, duration_value
		const audioCodecFactor = getter(data, Fields.audio_codec) ? 1 : 0.5;
		const width = getter(data, Fields.width);
		const height = getter(data, Fields.height);
		const errorFactor = getter(data, Fields.errors).length ? 0.25 : 1;
		const frameRate = getter(data, Fields.frame_rate);
		const duration = getter(data, Fields.duration_value) / 1000000;
		const score = audioCodecFactor * width * height * errorFactor * frameRate * duration;
		return Math.log(score);
	}

	getQuality(index) {
		return Videos.computeQuality(index, this.get);
	}

	getQualityFromLine(line) {
		return Videos.computeQuality(line, this.getFromLine);
	}

	getNameFromLine(line) {
		const metaTitle = this.getFromLine(line, Fields.meta_title);
		return metaTitle ? metaTitle : this.getFromLine(line, Fields.file_title);
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
		video.quality = this.getQuality(index);
		video.index = index;
		return video;
	}
}
