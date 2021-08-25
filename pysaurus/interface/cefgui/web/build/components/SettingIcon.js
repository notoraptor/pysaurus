System.register(["../utils/constants.js", "./MicroButton.js"], function (_export, _context) {
  "use strict";

  var Characters, MicroButton;

  function SettingIcon(props) {
    return /*#__PURE__*/React.createElement(MicroButton, {
      type: "settings",
      content: Characters.SETTINGS,
      title: props.title,
      action: props.action
    });
  }

  _export("SettingIcon", SettingIcon);

  return {
    setters: [function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
    }, function (_MicroButtonJs) {
      MicroButton = _MicroButtonJs.MicroButton;
    }],
    execute: function () {
      SettingIcon.propTypes = {
        title: PropTypes.string,
        action: PropTypes.func
      };
    }
  };
});