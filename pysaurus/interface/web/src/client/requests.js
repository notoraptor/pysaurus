let REQUEST_ID = 0;

function createRequest(name, parameters) {
	const request_id = REQUEST_ID;
	++REQUEST_ID;
	return {
		request_id: request_id,
		name: name,
		parameters: parameters || {}
	}
}

export class Request {
	static load() {
		return createRequest('load');
	}

	static valid_size() {
		return createRequest('valid_size');
	}

	static valid_length() {
		return createRequest('valid_length');
	}

	static nb(query) {
		return createRequest('nb', {query});
	}

	static nb_pages(query, page_size) {
		return createRequest('nb_pages', {query, page_size});
	}

	static database_info(page_size) {
		return createRequest('database_info', {page_size});
	}

	static list(field, reverse, page_size, page_number) {
		return createRequest('list', {field, reverse, page_size, page_number});
	}

	static image(video_id) {
		return createRequest('image', {video_id});
	}

	static image_filename(filename) {
		return createRequest('image_filename', {filename});
	}

	static open(video_id) {
		return createRequest('open', {video_id});
	}

	static clip(video_id, start, length) {
		return createRequest('clip', {video_id, start, length});
	}

	static open_filename(filename) {
		return createRequest('open_filename', {filename});
	}

	static rename_filename(filename, new_title) {
		return createRequest('rename_filename', {filename, new_title});
	}

	static delete_filename(filename) {
		return createRequest('delete_filename', {filename});
	}

	static clip_filename(filename, start, length) {
		return createRequest('clip_filename', {filename, start, length});
	}

	static videos() {
		return createRequest('videos');
	}
}
