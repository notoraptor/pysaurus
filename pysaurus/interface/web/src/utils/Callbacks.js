export class Callbacks {
	constructor() {
		this.callbacks = new Map();
		this.id = 1;
	}

	register(callback) {
		const id = this.id;
		this.callbacks.set(id, callback);
		++this.id;
		return id;
	}

	unregister(id) {
		this.callbacks.delete(id);
	}

	call(value) {
		for (let callback of this.callbacks.values()) {
			const toStop = callback(value);
			if (toStop) break;
		}
	}
}
