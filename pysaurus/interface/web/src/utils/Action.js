import {Shortcut} from "./Shortcut.js";

export class Action {
    /**
     * Initialize.
     * @param shortcut {string}
     * @param title {string}
     * @param callback {function}
     */
    constructor(shortcut, title, callback) {
        this.shortcut = new Shortcut(shortcut);
        this.title = title;
        this.callback = callback;
    }
}