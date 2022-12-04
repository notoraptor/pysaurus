export function python_call(name, ...args) {
	return window.backend_call(name, args);
}

export async function python_multiple_call(...calls) {
	let ret = null;
	for (let call of calls) {
		ret = await python_call(...call);
	}
	return ret;
}

export function backend_error(error) {
	const desc = error.string || `${error.name}: ${error.message}`;
	window.alert(desc);
}
