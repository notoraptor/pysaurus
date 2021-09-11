System.register(["./MicroButton.js"], function (_export, _context) {
  "use strict";

  var MicroButton;

  function PlusIcon(props) {
    return /*#__PURE__*/React.createElement(MicroButton, {
      type: "plus",
      content: "\u271A",
      title: props.title,
      action: props.action
    });
  }

  _export("PlusIcon", PlusIcon);

  return {
    setters: [function (_MicroButtonJs) {
      MicroButton = _MicroButtonJs.MicroButton;
    }],
    execute: function () {
      PlusIcon.propTypes = {
        title: PropTypes.string,
        action: PropTypes.func
      };
    }
  };
});