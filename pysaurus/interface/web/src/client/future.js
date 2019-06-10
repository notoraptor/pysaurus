export class Future {
	constructor() {
		this.__resolve_fn = null;
		this.__reject_fn = null;
		this.__promise = null;
		this.__done = false;

		const future = this;
		this.__promise = new Promise((resolve, reject) => {
			future.__resolve_fn = resolve;
			future.__reject_fn = reject;
		});
	}

	promise() {
		return this.__promise;
	}

	setResult(result) {
		if (!this.done()) {
			this.__done = true;
			const resolve_fn = this.__resolve_fn;
			if (resolve_fn)
				resolve_fn(result);
		}
	}

	setException(exception) {
		if (!this.done()) {
			this.__done = true;
			const reject_fn = this.__reject_fn;
			if (reject_fn)
				reject_fn(exception);
		}
	}

	done() {
		return this.__done;
	}
}