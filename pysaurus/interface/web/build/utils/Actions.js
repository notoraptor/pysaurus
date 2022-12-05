System.register(["../language.js"], function (_export, _context) {
  "use strict";

  var tr, Actions;

  _export("Actions", void 0);

  return {
    setters: [function (_languageJs) {
      tr = _languageJs.tr;
    }],
    execute: function () {
      _export("Actions", Actions = class Actions {
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
            if (shortcutToName.hasOwnProperty(shortcut)) throw new Error(tr("Duplicated shortcut {shortcut} for {name1} and {name2}", {
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