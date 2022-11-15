export function python_call(name, ...args) {
	return window.backend_call(name, args);
}

export function backend_error(error) {
	const desc = error.string || `${error.name}: ${error.message}`;
	window.alert(desc);
}
