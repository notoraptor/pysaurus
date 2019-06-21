const BYTES = 1;
const KILO_BYTES = 1024;
const MEGA_BYTES = KILO_BYTES * KILO_BYTES;
const GIGA_BYTES = KILO_BYTES * MEGA_BYTES;
const TERA_BYTES = KILO_BYTES * GIGA_BYTES;
const SIZE_UNIT_TO_STRING = {
	[BYTES]: 'b',
	[KILO_BYTES]: 'Kb',
	[MEGA_BYTES]: 'Mb',
	[GIGA_BYTES]: 'Gb',
	[TERA_BYTES]: 'Tb'
};

export class JavascriptFileSize {
	constructor(size) {
		this.size = size;
		this.unit = BYTES;
		for (let unit of [TERA_BYTES, GIGA_BYTES, MEGA_BYTES, KILO_BYTES]) {
			if (Math.floor(this.size / unit)) {
				this.unit = unit;
				break;
			}
		}
	}

	unitToString() {
		return SIZE_UNIT_TO_STRING[this.unit];
	}

	roundedSize() {
		return Math.round(this.size * 100 / this.unit) / 100;
	}

	toString() {
		return `${this.roundedSize()} ${this.unitToString()}`;
	}
}
