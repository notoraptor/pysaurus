import {Shortcut} from "./Shortcut.js";

function defaultIsActive() {
    return true;
}

export class Action {
    /**
     * Initialize.
     * @param shortcut {string}
     * @param title {string}
     * @param callback {function}
     * @param filter {function}
     */
    constructor(shortcut, title, callback, filter = undefined) {
        this.shortcut = new Shortcut(shortcut);
        this.title = title;
        this.callback = callback;
        this.isActive = filter || defaultIsActive;
    }
}
