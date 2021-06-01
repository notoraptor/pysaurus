System.register(["./Cross.js", "../utils/constants.js"], function (_export, _context) {
  "use strict";

  var Cross, Characters, SettingIcon;

  _export("SettingIcon", void 0);

  return {
    setters: [function (_CrossJs) {
      Cross = _CrossJs.Cross;
    }, function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
    }],
    execute: function () {
      _export("SettingIcon", SettingIcon = class SettingIcon extends Cross {
        constructor(props) {
          // action ? function()
          // title? str
          super(props);
          this.type = "settings";
          this.content = Characters.SETTINGS;
        }

      });
    }
  };
});