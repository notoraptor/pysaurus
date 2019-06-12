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

	static open(video_id) {
		return createRequest('open', {video_id});
	}
}
