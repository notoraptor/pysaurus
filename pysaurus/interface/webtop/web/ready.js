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

const KEYBOARD_MANAGER = new KeyboardManager();

class NotificationManager extends Callbacks {
    notify(notification) {
        for (let callback of this.getCallbacks()) {
            callback(notification);
        }
    }
}

const Notifications = new NotificationManager();

function __notify(notification) {
    return Notifications.notify(notification);
}

const Utils = {
    CHARACTER_CROSS: "\u2715",
    CHARACTER_SETTINGS: "\u2630",
    sentence: function(str) {
        if (str.length === 0)
            return str;
        if (str.length === 1)
            return str.toUpperCase();
        return str.substr(0, 1).toUpperCase() + str.substr(1);
    }
}

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
