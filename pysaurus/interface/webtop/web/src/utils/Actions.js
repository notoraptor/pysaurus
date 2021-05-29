export class Actions {
    /**
     * @param actions {Object.<string, Action>}
     */
    constructor(actions) {
        /** @type {Object.<string, Action>} */
        this.actions = actions;

        const shortcutToName = {};
        for (let name of Object.keys(actions)) {
            const shortcut = actions[name].shortcut.str;
            if (shortcutToName.hasOwnProperty(shortcut))
                throw new Error(`Duplicated shortcut ${shortcut} for ${shortcutToName[shortcut]} and ${name}`);
            shortcutToName[shortcut] = name;
        }
        this.onKeyPressed = this.onKeyPressed.bind(this);
    }

    /**
     * Callback to trigger shortcuts on keyboard events.
     * @param event {KeyboardEvent}
     * @returns {boolean}
     */
    onKeyPressed(event) {
        for (let action of Object.values(this.actions)) {
            if (action.shortcut.isPressed(event)) {
                setTimeout(() => action.callback(), 0);
                return true;
            }
        }
    }
}