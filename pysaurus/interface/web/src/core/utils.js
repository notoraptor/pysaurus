export const Utils = {
	UNICODE_BOTTOM_ARROW: '\u25BC',
	UNICODE_TOP_ARROW: '\u25B2',
	UNICODE_LEFT_ARROW: '\u25C0',
	UNICODE_RIGHT_ARROW: '\u25B6',
	strings: {
		DB_LOADING: 'DB_LOADING',
		DB_LOADED: 'DB_LOADED'
	},
	config: {
		HOSTNAME: 'localhost',
		PORT: 8432,
		PAGE_SIZES: [10, 20, 50, 100],
		DEFAULT_PAGE_SIZE: 100,
		MESSAGE_TIMEOUT_SECONDS: 100
	},
	getFileSeparator: function (path) {
		if (path.length >= 2 && path.charAt(1) === '\\')
			return '\\';
		return '/';
	},
	base64ToBlob: function (data) {
		const byteChars = atob(data);
		const byteNums = new Array(byteChars.length);
		for (let i = 0; i < byteChars.length; ++i) {
			byteNums[i] = byteChars.charCodeAt(i);
		}
		const byteArray = new Uint8Array(byteNums);
		return new Blob([byteArray]);
	},
	fileNameToURL: function (filename) {
		let fromWindows = filename.length >= 2 && filename.charAt(1) === ':';
		let prefix = '';
		let suffix = '';
		if (fromWindows) {
			prefix = filename.substr(0, 2);
			suffix = filename.substr(2);
		} else {
			prefix = '';
			suffix = filename;
		}
		suffix = suffix.replace(/\\/g, '/').split('/').map(piece => encodeURIComponent(piece)).join('/');
		return `${prefix}${suffix}`;
	}
};
