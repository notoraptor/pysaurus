System.register(["./Cross.js"], function (_export, _context) {
  "use strict";

  var Cross, PlusIcon;

  _export("PlusIcon", void 0);

  return {
    setters: [function (_CrossJs) {
      Cross = _CrossJs.Cross;
    }],
    execute: function () {
      _export("PlusIcon", PlusIcon = class PlusIcon extends Cross {
        constructor(props) {
          // action ? function()
          // title? str
          super(props);
          this.type = "plus";
          this.content = "\u271A";
        }

      });
    }
  };
});