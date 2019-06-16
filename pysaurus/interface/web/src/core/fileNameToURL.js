export function fileNameToURL(filename) {
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
