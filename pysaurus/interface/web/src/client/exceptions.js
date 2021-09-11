function createException(type, message) {
	return {type: type, message: message};
}

export class Exceptions {
	static fromErrorResponse(response) {
		return createException(response.error_type, response.message);
	}

	static disconnected() {
		return createException('disconnected', 'disconnected');
	}

	static connectionFailed() {
		return createException('connectionFailed', 'Unable to connect.');
	}

	static databaseFailed(message) {
		return createException('databaseFailed', message);
	}
}
