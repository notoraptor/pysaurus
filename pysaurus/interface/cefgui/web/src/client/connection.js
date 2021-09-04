import {Future} from "./future.js";
import {RequestContext} from "./requestContext.js";
import {Exceptions} from "./exceptions.js";

export const ConnectionStatus = {
	NOT_CONNECTED: 'not connected',
	CONNECTING: 'connecting',
	CONNECTED: 'connected'
};

export class Connection {
	constructor(hostname, port, useSSL) {
		if (useSSL)
			console.log(`Using SSL.`);
		// Public read-only attributes.
		this.protocol = useSSL ? 'wss' : 'ws';
		this.hostname = hostname;
		this.port = port;
		// Public properties.
		this.onError = null; // Callback onError(exception)
		this.onClose = null; // Callback onClose()
		this.onStatus = null; // Callback onStatus(status)
		this.onNotification = null;
		// Private attributes.
		this.socket = null;
		this.status = ConnectionStatus.NOT_CONNECTED;
		this.waitingRequests = {};
		this.notificationManagers = {};
		this.futureConnection = new Future();

		// Methods.
		this.getUrl = this.getUrl.bind(this);
		this.reset = this.reset.bind(this);
		this.connect = this.connect.bind(this);
		this.onOpen = this.onOpen.bind(this);
		this.onOpenError = this.onOpenError.bind(this);
		this.onSocketClose = this.onSocketClose.bind(this);
		this.onMessage = this.onMessage.bind(this);
		this.manageResponse = this.manageResponse.bind(this);
		this.manageNotification = this.manageNotification.bind(this);
		this.send = this.send.bind(this);
		this.setNotificationManager = this.setNotificationManager.bind(this);
	}

	getUrl() {
		return this.protocol + '://' + this.hostname + ':' + this.port;
	}

	setStatus(status) {
		this.status = status;
		if (this.onStatus)
			this.onStatus(status);
	}

	reset() {
		if (this.socket)
			this.socket.close();
		this.socket = null;
		this.status = ConnectionStatus.NOT_CONNECTED;
		for (let requestContext of Object.values(this.waitingRequests)) {
			requestContext.future.setException(Exceptions.disconnected());
		}
		if (!this.futureConnection.done())
			this.futureConnection.setException(Exceptions.disconnected());
		this.waitingRequests = {};
		this.futureConnection = new Future();
		// We don't reset notification managers, callbacks and address.
	}

	connect() {
		this.status = ConnectionStatus.CONNECTING;
		this.socket = new WebSocket(this.getUrl());
		this.socket.onopen = this.onOpen;
		this.socket.onerror = this.onOpenError;
		return this.futureConnection.promise();
	}

	onOpen() {
		this.status = ConnectionStatus.CONNECTED;
		this.socket.onmessage = this.onMessage;
		if (this.onError)
			this.socket.onerror = this.onError;
		else
			this.socket.onerror = null;
		this.socket.onclose = this.onSocketClose;
		this.futureConnection.setResult(null);
	}

	onOpenError(error) {
		console.error(error);
		this.status = ConnectionStatus.NOT_CONNECTED;
		this.futureConnection.setException(Exceptions.connectionFailed());
	}

	onSocketClose() {
		this.status = ConnectionStatus.NOT_CONNECTED;
		if (this.onClose)
			this.onClose();
	}

	onMessage(event) {
		try {
			const message = JSON.parse(event.data);
			if (!message.hasOwnProperty('message_type')) {
				return console.error('Unable to infer received message type.');
			}
			if (message.message_type === 'response') {
				this.manageResponse(message);
			} else if (message.message_type === 'notification') {
				this.manageNotification(message);
			} else {
				return console.error(`Unknown message type ${message.message_type}`);
			}
		} catch (error) {
			console.error(error);
		}
	}

	manageResponse(response) {
		if (!response.hasOwnProperty('request_id'))
			throw new Error(`Response does not have request ID.`);
		if (!response.hasOwnProperty('type'))
			throw new Error('Response does not have type.');
		if (!this.waitingRequests.hasOwnProperty(response.request_id))
			throw new Error(`Unknown response request ID: ${response.request_id}`);
		const requestContext = this.waitingRequests[response.request_id];
		/** @var RequestContext requestContext */
		delete this.waitingRequests[response.request_id];
		switch (response.type) {
			case 'ok':
				requestContext.future.setResult(null);
				break;
			case 'data':
				if (!response.hasOwnProperty('data_type') || response.data_type !== requestContext.request.name)
					throw new Error('Invalid data type for received data response.');
				if (!response.hasOwnProperty('data'))
					throw new Error('No data field for received data response.');
				requestContext.future.setResult(response.data);
				break;
			case 'error':
				if (!response.hasOwnProperty('error_type'))
					throw new Error('Error response missing field error_type.');
				if (!response.hasOwnProperty('message'))
					throw new Error('Error response missing field message.');
				requestContext.future.setException(Exceptions.fromErrorResponse(response));
				break;
			default:
				throw new Error(`Invalid response type: ${response.type}`);
		}
	}

	manageNotification(notification) {
		if (!notification.hasOwnProperty('name'))
			throw new Error('Missing notification name.');
		if (!notification.hasOwnProperty('parameters'))
			throw new Error('Missing notification parameters.');
		if (this.notificationManagers.hasOwnProperty(notification.name)) {
			const callback = this.notificationManagers[notification.name];
			callback(notification.parameters);
		} else if (this.onNotification) {
			this.onNotification(notification);
		}
	}

	send(request) {
		if (this.status !== ConnectionStatus.CONNECTED)
			throw new Error('Socket not yet opened.');
		if (this.waitingRequests.hasOwnProperty(request.request_id))
			throw new Error(`Request ID already used: ${request.request_id}`);
		const requestContext = new RequestContext(request);
		this.waitingRequests[requestContext.getRequestID()] = requestContext;
		this.socket.send(JSON.stringify(request));
		return requestContext.future.promise();
	}

	setNotificationManager(name, callback) {
		if (callback)
			this.notificationManagers[name] = callback;
		else if (this.notificationManagers.hasOwnProperty(name))
			delete this.notificationManagers[name];
	}
}
