export function python_call(name, ...args) {
    return window.backend_call(name, args);
}

export function backend_error(error) {
    window.alert(`Backend error: ${error.name}: ${error.message}`);
}

