export const Utils = {
	UNICODE_BOTTOM_ARROW: '\u25BC',
	UNICODE_TOP_ARROW: '\u25B2',
	UNICODE_LEFT_ARROW: '\u25C0',
	UNICODE_RIGHT_ARROW: '\u25B6',
	getFileSeparator: function (path) {
		if (path.length >= 2 && path.charAt(1) === '\\')
			return '\\';
		return '/';
	}
};