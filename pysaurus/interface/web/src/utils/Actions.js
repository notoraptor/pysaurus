export class Actions {
    /**
     * @param actions {Object.<string, Action>}
     * @param context {Object}
     */
    constructor(actions, context) {
        /** @type {Object.<string, Action>} */
        this.actions = actions;

        const shortcutToName = {};
        for (let name of Object.keys(actions)) {
            const shortcut = actions[name].shortcut.str;
            if (shortcutToName.hasOwnProperty(shortcut))
                throw new Error(context.error_duplicated_shortcut.format({shortcut: shortcut, name1: shortcutToName[shortcut], name2: name}));
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
            if (action.isActive() && action.shortcut.isPressed(event)) {
                setTimeout(() => action.callback(), 0);
                return true;
            }
        }
    }
}
