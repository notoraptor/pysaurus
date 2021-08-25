System.register(["./Cross.js", "../utils/Action.js"], function (_export, _context) {
  "use strict";

  var Cross, Action;

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
    }, function (_utilsActionJs) {
      Action = _utilsActionJs.Action;
    }],
    execute: function () {
      ActionToCross.propTypes = {
        action: PropTypes.instanceOf(Action),
        title: PropTypes.string
      };
    }
  };
});