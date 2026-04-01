System.register(["./Shortcut.js"], function (_export, _context) {
  "use strict";

  var Shortcut, Action;
  function defaultIsActive() {
    return true;
  }
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
         * @param filter {function}
         */
        constructor(shortcut, title, callback, filter = undefined) {
          this.shortcut = new Shortcut(shortcut);
          this.title = title;
          this.callback = callback;
          this.isActive = filter || defaultIsActive;
        }
      });
    }
  };
});