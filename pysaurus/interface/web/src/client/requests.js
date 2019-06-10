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
}