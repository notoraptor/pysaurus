export function python_call(name, ...args) {
	return window.backend_call(name, args);
}

export async function python_multiple_call(...calls) {
	const outs = [];
	for (let call of calls) {
		const ret = await python_call(...call);
		if (ret !== null) outs.push(ret);
	}
	return outs.length ? (outs.length === 1 ? outs[0] : outs) : null;
}

export function backend_error(error) {
	const desc = error.string || `${error.name}: ${error.message}`;
	window.alert(desc);
}
