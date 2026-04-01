import { Callbacks } from "./Callbacks.js";

const GENERIC_CALLBACK_NAME = "notify";

export class NotificationManager {
	constructor() {
		this.callbacks = new Callbacks();
		this.notificationCallbacks = new Map();
		this.callbackIDToNotification = new Map();
	}

	installFrom(object) {
		// console.log(`Installing from ${object.constructor.name}`);
		const callbackIndices = [];
		for (let name of Object.getOwnPropertyNames(Object.getPrototypeOf(object)).filter(
			(name) =>
				object[name] instanceof Function &&
				(name === GENERIC_CALLBACK_NAME ||
					(name.length && name.charAt(0) === name.charAt(0).toUpperCase()) ||
					(name.length > 2 && name.startsWith("on"))),
		)) {
			const element = object[name];
			const notificationName = name.startsWith("on") ? name.substring(2) : name;
			const callbackID = this.callbacks.register(element);
			callbackIndices.push(callbackID);
			if (!this.notificationCallbacks.has(notificationName)) {
				this.notificationCallbacks.set(notificationName, []);
			}
			this.notificationCallbacks.get(notificationName).push(callbackID);
			this.callbackIDToNotification.set(callbackID, notificationName);
			// console.log(`[notif/cbk:${callbackID}] ${object.constructor.name}: on ${notificationName}`);
		}
		object.__notification_manager_data = callbackIndices;
	}

	uninstallFrom(object) {
		for (let callbackID of object.__notification_manager_data) {
			this.callbacks.unregister(callbackID);
			const notificationName = this.callbackIDToNotification.get(callbackID);
			this.callbackIDToNotification.delete(callbackID);
			const oldNotifCbIDs = this.notificationCallbacks.get(notificationName);
			this.notificationCallbacks.delete(notificationName);
			const newNotifCbIDs = oldNotifCbIDs.filter((cbId) => cbId !== callbackID);
			if (newNotifCbIDs.length) {
				this.notificationCallbacks.set(notificationName, newNotifCbIDs);
			}
			// console.log(`[removed/notif/cbk:${callbackID}] ${object.constructor.name}: on ${notificationName}`);
		}
		object.__notification_manager_data = [];
	}

	call(notification) {
		const name = notification.name;
		let callbackIndices = null;
		let usedName;
		if (this.notificationCallbacks.has(name)) {
			callbackIndices = this.notificationCallbacks.get(name);
			usedName = name;
		} else if (this.notificationCallbacks.has(GENERIC_CALLBACK_NAME)) {
			callbackIndices = this.notificationCallbacks.get(GENERIC_CALLBACK_NAME);
			usedName = GENERIC_CALLBACK_NAME;
		}
		if (callbackIndices) {
			for (let callbackID of callbackIndices) {
				const callback = this.callbacks.callbacks.get(callbackID);
				callback(notification);
			}
		} else {
			// console.warn(`Unhandled notification: ${name}: ${JSON.stringify(notification)}`);
		}
	}
}
