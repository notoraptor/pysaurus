System.register(["./Cross.js"], function (_export, _context) {
  "use strict";

  var Cross;

  /**
   * @param props {{action: Action, title: str?}}
   */
  function ActionToCross(props) {
    const {
      action,
      title
    } = props;
    return /*#__PURE__*/React.createElement(Cross, {
      title: `${title || action.title} (${action.shortcut.str})`,
      action: action.callback
    });
  }

  _export("ActionToCross", ActionToCross);

  return {
    setters: [function (_CrossJs) {
      Cross = _CrossJs.Cross;
    }],
    execute: function () {}
  };
});