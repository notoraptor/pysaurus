System.register(["../utils/constants.js", "./MicroButton.js"], function (_export, _context) {
  "use strict";

  var Characters, MicroButton;
  function Cross(props) {
    return /*#__PURE__*/React.createElement(MicroButton, {
      type: "cross",
      content: Characters.CROSS,
      title: props.title,
      action: props.action
    });
  }
  _export("Cross", Cross);
  return {
    setters: [function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
    }, function (_MicroButtonJs) {
      MicroButton = _MicroButtonJs.MicroButton;
    }],
    execute: function () {
      Cross.propTypes = {
        title: PropTypes.string,
        action: PropTypes.func
      };
    }
  };
});