System.register(["./Shortcut.js"], function (_export, _context) {
  "use strict";

  var Shortcut, Action;

  _export("Action", void 0);

  return {
    setters: [function (_ShortcutJs) {
      Shortcut = _ShortcutJs.Shortcut;
    }],
    execute: function () {
      _export("Action", Action = class Action {
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

      });
    }
  };
});