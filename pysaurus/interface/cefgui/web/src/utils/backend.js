export function python_call(name, ...args) {
    return new Promise((resolve, reject) => {
        python.call(name, args, resolve, reject);
    });
}

export function backend_error(error) {
    window.alert(`Backend error: ${error.name}: ${error.message}`);
}

