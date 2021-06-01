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

/**
 * NOTIFICATION_MANAGER.call is called from Python to send notifications to interface.
 * @type {Callbacks}
 */
const NOTIFICATION_MANAGER = new Callbacks();

let APP = null;
/** @type App */

window.onload = function() {
    System.import('./build/index.js');
};
