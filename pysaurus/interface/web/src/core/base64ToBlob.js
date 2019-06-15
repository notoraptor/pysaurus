export function base64ToBlob(data) {
	const byteChars = atob(data);
	const byteNums = new Array(byteChars.length);
	for (let i = 0; i < byteChars.length; ++i) {
		byteNums[i] = byteChars.charCodeAt(i);
	}
	const byteArray = new Uint8Array(byteNums);
	return new Blob([byteArray]);
}
