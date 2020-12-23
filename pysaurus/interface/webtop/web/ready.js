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
        this.id = 1;
        this.mapping = {};
        this.order = [];
    }
    register(callback) {
        const id = this.id;
        this.mapping[id] = callback;
        this.order.push(id);
        ++this.id;
        return id;
    }
    unregister(id) {
        if (this.mapping[id])
            this.mapping[id] = undefined;
        const order = [];
        for (let value of this.order) {
            if (value !== id)
                order.push(value);
        }
        this.order = order;
    }
    getCallbacks() {
        return this.order.map(id => this.mapping[id]);
    }
}

class KeyboardManager extends Callbacks {
    manage(event) {
        for (let callback of this.getCallbacks()) {
            const toStop = callback(event);
            if (toStop)
                break;
        }
    }
}

class NotificationManager extends Callbacks {
    notify(notification) {
        for (let callback of this.getCallbacks()) {
            callback(notification);
        }
    }
}

const KEYBOARD_MANAGER = new KeyboardManager();

const Notifications = new NotificationManager();

/**
 * Called from Python to send notifications to interface.
 */
function __notify(notification) {
    return Notifications.notify(notification);
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
    KEYBOARD_MANAGER.manage(event);
};
document.body.onunload = function() {
    console.info('GUI closed!');
    python_call('close_app');
};
