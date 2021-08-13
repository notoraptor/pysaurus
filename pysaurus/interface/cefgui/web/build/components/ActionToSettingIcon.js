System.register(["./SettingIcon.js"], function (_export, _context) {
  "use strict";

  var SettingIcon;

  /**
   * @param props {{action: Action, title: str?}}
   */
  function ActionToSettingIcon(props) {
    const {
      action,
      title
    } = props;
    return /*#__PURE__*/React.createElement(SettingIcon, {
      title: `${title || action.title} (${action.shortcut.str})`,
      action: action.callback
    });
  }

  _export("ActionToSettingIcon", ActionToSettingIcon);

  return {
    setters: [function (_SettingIconJs) {
      SettingIcon = _SettingIconJs.SettingIcon;
    }],
    execute: function () {}
  };
});