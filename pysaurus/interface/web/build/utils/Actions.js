System.register(["./functions.js"], function (_export, _context) {
  "use strict";

  var formatString, Actions;

  _export("Actions", void 0);

  return {
    setters: [function (_functionsJs) {
      formatString = _functionsJs.formatString;
    }],
    execute: function () {
      _export("Actions", Actions = class Actions {
        /**
         * @param actions {Object.<string, Action>}
         */
        constructor(actions) {
          /** @type {Object.<string, Action>} */
          this.actions = actions;
          const shortcutToName = {};

          for (let name of Object.keys(actions)) {
            const shortcut = actions[name].shortcut.str;
            if (shortcutToName.hasOwnProperty(shortcut)) throw new Error(formatString(PYTHON_LANG.error_duplicated_shortcut, {
              shortcut: shortcut,
              name1: shortcutToName[shortcut],
              name2: name
            }));
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

      });
    }
  };
});