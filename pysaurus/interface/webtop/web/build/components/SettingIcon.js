System.register(["./Cross.js"], function (_export, _context) {
  "use strict";

  var Cross, SettingIcon;

  _export("SettingIcon", void 0);

  return {
    setters: [function (_CrossJs) {
      Cross = _CrossJs.Cross;
    }],
    execute: function () {
      _export("SettingIcon", SettingIcon = class SettingIcon extends Cross {
        constructor(props) {
          // action ? function()
          // title? str
          super(props);
          this.type = "settings";
          this.content = Utils.CHARACTER_SETTINGS;
        }

      });
    }
  };
});