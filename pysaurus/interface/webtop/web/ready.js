function python_call(name, ...args) {
    return new Promise((resolve, reject) => {
        python.call(name, args, resolve, reject);
    });
}

function backend_error(error) {
    window.alert(`Backend error: ${error.name}: ${error.message}`);
}

class Callbacks {
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
            if (toStop)
                break;
        }
    }
}

const KEYBOARD_MANAGER = new Callbacks();
const NOTIFICATION_MANAGER = new Callbacks();

/**
 * Called from Python to send notifications to interface.
 */
function __notify(notification) {
    NOTIFICATION_MANAGER.call(notification);
}

const Utils = {
    CHARACTER_CROSS: "\u2715",
    CHARACTER_SETTINGS: "\u2630",
    CHARACTER_ARROW_DOWN: "\u25BC",
    CHARACTER_ARROW_UP: "\u25B2",
    CHARACTER_SMART_ARROW_LEFT: "\u2B9C",
    CHARACTER_SMART_ARROW_RIGHT: "\u2B9E",
    sentence: function(str) {
        if (str.length === 0)
            return str;
        if (str.length === 1)
            return str.toUpperCase();
        return str.substr(0, 1).toUpperCase() + str.substr(1);
    }
}

function propertyValueToString(propType, value) {
    if (['bool', 'int', 'float'].indexOf(propType) >= 0)
        return value;
    return value.length ? value: null;
}

/**
 * @param propType {string}
 * @param propEnum {Array}
 * @param value {string}
 * @returns {null}
 */
function parsePropValString(propType, propEnum, value) {
    let parsed = null;
    switch (propType) {
        case "bool":
            if (value === "false")
                parsed = false;
            else if (value === "true")
                parsed = true;
            else
                throw `Invalid bool value, expected: [false, true], got ${value}`;
            break;
        case "int":
            parsed = parseInt(value);
            if(isNaN(parsed))
                throw `Unable to parse integer: ${value}`;
            break;
        case "float":
            parsed = parseFloat(value);
            if (isNaN(parsed))
                throw `Unable to parse floating value: ${value}`;
            break;
        case "str":
            parsed = value;
            break;
        default:
            throw `Unknown property type: ${propType}`;
    }
    if (propEnum && propEnum.indexOf(parsed) < 0)
        throw `Invalid enum value, expected: [${propEnum.join(', ')}], got ${value}`;
    return parsed;
}

let APP = null;
/** @type App */

window.onload = function() {
    System.import('./build/index.js');
};
window.onkeydown = function(event) {
    KEYBOARD_MANAGER.call(event);
};
document.body.onunload = function() {
    console.info('GUI closed!');
    python_call('close_app');
};
