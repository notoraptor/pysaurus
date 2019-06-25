import {JavascriptDuration} from "./javascriptDuration";
import {JavascriptFileSize} from "./javascriptFileSize";

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
	filename: 'Path',
	container_format: 'Format',
	audio_codec: 'Audio codec',
	video_codec: 'Video codec',
	width: 'Width',
	height: 'Height',
	sample_rate: 'Sample rate',
	audio_bit_rate: 'Audio bit rate',
	frame_rate: 'Frame rate',
	duration_value: 'Duration',
	size_value: 'Size',
	date_value: 'Date',
	meta_title: 'Title (meta tag)',
	file_title: 'Title (file name)',
	extension: 'Extension',
	name: 'Title',
	quality: 'Quality'
};

export const SearchType = {
	exact: 'exact',
	all: 'all',
	any: 'any'
};

export const Extra = {
	image64: 'image64'
};

export class Videos {
	constructor(table) {
		/** @var Array table */
		// Fields.
		this.headers = null;
		this.fieldIndex = {};
		this.database = {};
		this.lines = null;
		this.viewIsDatabase = null;
		this.extras = {};
		this.sortField = null;
		this.sortReverse = false;
		this.nbUpdates = 0;
		// Functions.
		this.get = this.get.bind(this);
		this.__getFromLine = this.__getFromLine.bind(this);
		// Initialization.
		this.headers = table.shift();
		for (let i = 0; i < this.headers.length; ++i) {
			this.fieldIndex[this.headers[i]] = i;
		}
		this.fieldIndex[SpecialFields.id] = this.headers.length;
		for (let i = 0; i < table.length; ++i) {
			const line = table[i];
			line.push(i);
			this.database[i] = line;
		}
		this.lines = Object.values(this.database);
		this.viewIsDatabase = true;
	}

	static computeName(data, getter) {
		const metaTitle = getter(data, Fields.meta_title);
		return metaTitle ? metaTitle : getter(data, Fields.file_title);
	}

	static computeQuality(data, getter) {
		const width = getter(data, Fields.width);
		const height = getter(data, Fields.height);
		const frameRate = getter(data, Fields.frame_rate);
		const nbSeconds = getter(data, Fields.duration_value) / 1000000;
		const audioBitrate = getter(data, Fields.audio_bit_rate);
		const hasErrors = getter(data, Fields.errors).length;
		const totalRelevantBytes = (width * height * frameRate * nbSeconds * 3) + ((audioBitrate * nbSeconds) / 8);
		const rawQuality = hasErrors ? Math.sqrt(totalRelevantBytes) : totalRelevantBytes;
		return rawQuality ? Math.log(rawQuality) : 0;
	}

	__getName(index) {
		return Videos.computeName(index, this.get);
	}

	__getQuality(index) {
		return Videos.computeQuality(index, this.get);
	}

	__getNameFromLine(line) {
		return Videos.computeName(line, this.__getFromLine);
	}

	__getQualityFromLine(line) {
		return Videos.computeQuality(line, this.__getFromLine);
	}

	__getFromLine(line, field) {
		if (field === 'name')
			return this.__getNameFromLine(line);
		if (field === 'quality')
			return this.__getQualityFromLine(line);
		return line[this.fieldIndex[field]];
	}

	get(index, field) {
		if (field === 'name')
			return this.__getName(index);
		if (field === 'quality')
			return this.__getQuality(index);
		return this.lines[index][this.fieldIndex[field]];
	}

	getExtra(index, field) {
		const filename = this.get(index, Fields.filename);
		if (this.extras.hasOwnProperty(filename) && this.extras[filename].hasOwnProperty(field))
			return this.extras[filename][field];
		return null;
	}

	getDatabaseIdentifiers() {
		return Object.keys(this.database);
	}

	getFromDatabase(identifier, field) {
		return this.__getFromLine(this.database[identifier], field);
	}

	getExtraFromDatabase(identifier, field) {
		const filename = this.getFromDatabase(identifier, Fields.filename);
		if (this.extras.hasOwnProperty(filename) && this.extras[filename].hasOwnProperty(field))
			return this.extras[filename][field];
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
			Fields.size_value,
			Fields.size_string,
			Fields.date_string,
			Fields.extension,
		]) {
			video[field] = this.get(index, field);
		}
		video.frame_rate = Math.round(video.frame_rate);
		video.audio_bit_rate = `${Math.round(video.audio_bit_rate / 1000)} Kb/s`;
		video.name = this.__getName(index);
		video.quality = Math.round(this.__getQuality(index) * 100) / 100;
		video.index = index;
		return video;
	}

	hasView() {
		return !this.viewIsDatabase;
	}

	size() {
		return this.lines.length;
	}

	duration() {
		let totalMicroseconds = 0;
		for (let line of this.lines)
			totalMicroseconds += this.__getFromLine(line, Fields.duration_value);
		return new JavascriptDuration(totalMicroseconds);
	}

	fileSize() {
		let totalSize = 0;
		for (let line of this.lines)
			totalSize += this.__getFromLine(line, Fields.size_value);
		return new JavascriptFileSize(totalSize);
	}

	nbPages(pageSize) {
		return Math.floor(this.size() / pageSize) + (this.size() % pageSize ? 1 : 0);
	}

	databaseSize() {
		return Object.keys(this.database).length;
	}

	databaseDuration() {
		let totalMicroseconds = 0;
		for (let line of Object.values(this.database))
			totalMicroseconds += this.__getFromLine(line, Fields.duration_value);
		return new JavascriptDuration(totalMicroseconds);
	}

	databaseFileSize() {
		let totalSize = 0;
		for (let line of Object.values(this.database))
			totalSize += this.__getFromLine(line, Fields.size_value);
		return new JavascriptFileSize(totalSize);
	}

	__find(sequence, searchType) {
		const found = [];
		if (!sequence || !searchType || !SearchType.hasOwnProperty(searchType))
			return found;
		sequence = sequence.toLocaleLowerCase();
		if (searchType === SearchType.exact) {
			for (let line of Object.values(this.database)) {
				for (let fieldName of Object.keys(Fields)) {
					const fieldValue = `${this.__getFromLine(line, fieldName)}`.toLocaleLowerCase();
					if (fieldValue.indexOf(sequence) >= 0) {
						found.push(line);
						break;
					}
				}
			}
		} else {
			const terms = sequence.split(/[ \t\r\n\b\v]+/).map(term => term.toLocaleLowerCase());
			if (searchType === SearchType.all) {
				for (let line of Object.values(this.database)) {
					let allTermsFound = true;
					for (let term of terms) {
						let termFound = false;
						for (let fieldName of Object.keys(Fields)) {
							const fieldValue = `${this.__getFromLine(line, fieldName)}`.toLocaleLowerCase();
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
						found.push(line);
				}
			} else { // Any.
				for (let line of Object.values(this.database)) {
					let anyTermFound = false;
					for (let term of terms) {
						for (let fieldName of Object.keys(Fields)) {
							const fieldValue = `${this.__getFromLine(line, fieldName)}`.toLocaleLowerCase();
							if (fieldValue.indexOf(term) >= 0) {
								anyTermFound = true;
								break;
							}
						}
						if (anyTermFound)
							break;
					}
					if (anyTermFound)
						found.push(line);
				}
			}
		}
		return found;
	}

	setSearch(sequence, searchType) {
		let changed = false;
		if (!sequence || !searchType || !SearchType.hasOwnProperty(searchType)) {
			if (!this.viewIsDatabase) {
				this.lines = Object.values(this.database);
				this.viewIsDatabase = true;
				changed = true;
			}
		} else {
			this.lines = this.__find(sequence, searchType);
			this.viewIsDatabase = false;
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

	remove(index) {
		if (index >= 0 && index < this.lines.length) {
			const filename = this.get(index, Fields.filename);
			const id = this.get(index, SpecialFields.id);
			delete this.database[id];
			this.lines.splice(index, 1);
			if (this.extras.hasOwnProperty(filename))
				delete this.extras[filename];
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
			}
			this.lines[index][this.fieldIndex[Fields.filename]] = newFilename;
			this.lines[index][this.fieldIndex[Fields.file_title]] = newFileTitle;
			if (extra)
				this.extras[newFilename] = extra;
			++this.nbUpdates;
		}
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
			let valueA = this.__getFromLine(a, field);
			let valueB = this.__getFromLine(b, field);
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

	findSameValues(field) {
		const groups = {};
		let dbSize = 0;
		for (let line of Object.values(this.database)) {
			++dbSize;
			const value = this.__getFromLine(line, field);
			if (!groups.hasOwnProperty(value))
				groups[value] = [];
			groups[value].push(line);
		}
		const countGroups = Object.keys(groups).length;
		if (countGroups === 0 || countGroups === 1 || countGroups === dbSize)
			return 0;
		const lines = [];
		for (let groupedLines of Object.values(groups)) {
			if (groupedLines.length > 1)
				lines.push(...groupedLines);
		}
		if (lines.length) {
			this.lines = lines;
			this.viewIsDatabase = false;
		}
		return lines.length;
	}
}
