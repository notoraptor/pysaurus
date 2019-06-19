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

export const SpecialFields = {id: 'id'};

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

export const SearchType = {
	exact: 'exact',
	all: 'all',
	any: 'any'
};

export const Extra = {
	image64: 'image64',
	newName: 'newName'
};

export class Videos {
	constructor(table) {
		/** @var Array table */
		this.headers = table.shift();
		this.database = table;
		for (let i = 0; i < this.database.length; ++i)
			this.database[i].push(i);
		this.lines = this.database;
		this.extras = {};
		this.fieldIndex = {};
		for (let i = 0; i < this.headers.length; ++i) {
			this.fieldIndex[this.headers[i]] = i;
		}
		this.fieldIndex[SpecialFields.id] = this.headers.length;
		this.sortField = null;
		this.sortReverse = false;
		this.nbUpdates = 0;
		this.get = this.get.bind(this);
		this.getFromLine = this.getFromLine.bind(this);
	}

	find(sequence, searchType) {
		const found = [];
		if (!sequence || !searchType || !SearchType.hasOwnProperty(searchType))
			return found;
		sequence = sequence.toLocaleLowerCase();
		if (searchType === SearchType.exact) {
			for (let i = 0; i < this.database.length; ++i) {
				for (let fieldName of Object.keys(Fields)) {
					const fieldValue = `${this.getFromLine(this.database[i], fieldName)}`.toLocaleLowerCase();
					if (fieldValue.indexOf(sequence) >= 0) {
						found.push(this.database[i]);
						break;
					}
				}
			}
		} else {
			const terms = sequence.split(/[ \t\r\n\b\v]+/).map(term => term.toLocaleLowerCase());
			if (searchType === SearchType.all) {
				for (let i = 0; i < this.database.length; ++i) {
					let allTermsFound = true;
					for (let term of terms) {
						let termFound = false;
						for (let fieldName of Object.keys(Fields)) {
							const fieldValue = `${this.getFromLine(this.database[i], fieldName)}`.toLocaleLowerCase();
							if (fieldValue.indexOf(term) >= 0) {
								termFound = true;
								break;
							}
						}
						if (!termFound) {
							allTermsFound = false;
							break;
						}
					}
					if (allTermsFound)
						found.push(this.database[i]);
				}
			} else { // Any.
				for (let i = 0; i < this.database.length; ++i) {
					let anyTermFound = false;
					for (let term of terms) {
						for (let fieldName of Object.keys(Fields)) {
							const fieldValue = `${this.getFromLine(this.database[i], fieldName)}`.toLocaleLowerCase();
							if (fieldValue.indexOf(term) >= 0) {
								anyTermFound = true;
								break;
							}
						}
						if (anyTermFound)
							break;
					}
					if (anyTermFound)
						found.push(this.database[i]);
				}
			}
		}
		return found;
	}

	setSearch(sequence, searchType) {
		let changed = false;
		if (!sequence || !searchType || !SearchType.hasOwnProperty(searchType)) {
			if (this.lines !== this.database) {
				this.lines = this.database;
				changed = true;
			}
		} else {
			this.lines = this.find(sequence, searchType);
			changed = true;
		}
		if (changed) {
			const sortField = this.sortField;
			const sortReverse = this.sortReverse;
			this.sortField = null;
			this.sortReverse = null;
			this.sort(sortField, sortReverse);
		}
		return changed;
	}

	static computeName(data, getter) {
		const metaTitle = getter(data, Fields.meta_title);
		return metaTitle ? metaTitle : getter(data, Fields.file_title);
	}

	static computeQuality(data, getter) {
		// !!audio_codec, width, height, !errors.length, frame_rate, duration_value
		const audioCodecFactor = getter(data, Fields.audio_codec) ? 1 : 0.5;
		const width = getter(data, Fields.width);
		const height = getter(data, Fields.height);
		const errorFactor = getter(data, Fields.errors).length ? 0.25 : 1;
		const frameRate = Math.pow(getter(data, Fields.frame_rate), 2);
		const duration = getter(data, Fields.duration_value) / 1000000;
		const audioBitrate = Math.log(getter(data, Fields.audio_bit_rate) / 1000 || 1);
		const score = audioCodecFactor * width * height * errorFactor * frameRate * duration * audioBitrate;
		return Math.log(score);
	}

	getName(index) {
		return Videos.computeName(index, this.get);
	}

	getQuality(index) {
		return Videos.computeQuality(index, this.get);
	}

	getNameFromLine(line) {
		return Videos.computeName(line, this.getFromLine);
	}

	getQualityFromLine(line) {
		return Videos.computeQuality(line, this.getFromLine);
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
		video.audio_bit_rate = `${Math.round(video.audio_bit_rate / 1000)} Kb/s`;
		video.name = this.getName(index);
		video.quality = Math.round(this.getQuality(index) * 100) / 100;
		video.index = index;
		return video;
	}

	size() {
		return this.lines.length;
	}

	databaseSize() {
		return this.database.length;
	}

	setExtra(index, field, value) {
		const filename = this.get(index, Fields.filename);
		if (!this.extras.hasOwnProperty(filename))
			this.extras[filename] = {};
		this.extras[filename][field] = value;
		++this.nbUpdates;
	}

	sort(field, reverse) {
		reverse = !!reverse;
		if (this.sortField === field && this.sortReverse === reverse)
			return;

		this.lines.sort((a, b) => {
			let valueA = this.getFromLine(a, field);
			let valueB = this.getFromLine(b, field);
			let ret = 0;
			if (typeof valueA === 'string') {
				ret = valueA.toLocaleLowerCase().localeCompare(valueB.toLocaleLowerCase());
				if (ret === 0)
					ret = valueA.localeCompare(valueB);
			} else if (valueA < valueB)
				ret = -1;
			else if (valueA > valueB)
				ret = 1;
			return reverse ? -ret : ret;
		});
		this.sortField = field;
		this.sortReverse = reverse;
		++this.nbUpdates;
	}

	remove(index) {
		if (index >= 0 && index < this.lines.length) {
			const filename = this.get(index, Fields.filename);
			if (this.extras.hasOwnProperty(filename))
				delete this.extras[filename];
			if (this.lines !== this.database) {
				const id = this.get(index, SpecialFields.id);
				this.database.splice(id, 1);
			}
			this.lines.splice(index, 1);
			++this.nbUpdates;
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
			++this.nbUpdates;
		}
	}
}
