import {formatString} from "./functions.js";

export function python_call(name, ...args) {
    return window.backend_call(name, args);
}

export function backend_error(error) {
    window.alert(formatString(PYTHON_LANG.backend_error, {name: error.name, message: error.message}));
}

