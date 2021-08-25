System.register(["./SettingIcon.js", "../utils/Action.js"], function (_export, _context) {
  "use strict";

  var SettingIcon, Action;

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
    }, function (_utilsActionJs) {
      Action = _utilsActionJs.Action;
    }],
    execute: function () {
      ActionToSettingIcon.propTypes = {
        action: PropTypes.instanceOf(Action),
        title: PropTypes.string
      };
    }
  };
});