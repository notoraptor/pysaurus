import {Future} from "./future.js";

export class RequestContext {
	constructor(request) {
		this.request = request;
		this.future = new Future();
	}

	getRequestID() {
		return this.request.request_id;
	}
}
