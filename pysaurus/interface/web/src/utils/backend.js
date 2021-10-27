export function python_call(name, ...args) {
    return window.backend_call(name, args);
}

export function backend_error(error) {
    window.alert(PYTHON_LANG.backend_error.format({name: error.name, message: error.message}));
}

