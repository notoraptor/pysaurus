System.register(["../utils/Action.js", "./SettingIcon.js"], function (_export, _context) {
  "use strict";

  var Action, SettingIcon;
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
    setters: [function (_utilsActionJs) {
      Action = _utilsActionJs.Action;
    }, function (_SettingIconJs) {
      SettingIcon = _SettingIconJs.SettingIcon;
    }],
    execute: function () {
      ActionToSettingIcon.propTypes = {
        action: PropTypes.instanceOf(Action),
        title: PropTypes.string
      };
    }
  };
});