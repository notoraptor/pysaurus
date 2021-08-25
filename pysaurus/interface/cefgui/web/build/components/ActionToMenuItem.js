System.register(["./MenuItem.js", "../utils/Action.js"], function (_export, _context) {
  "use strict";

  var MenuItem, Action;

  function ActionToMenuItem(props) {
    const {
      action,
      title
    } = props;
    return /*#__PURE__*/React.createElement(MenuItem, {
      shortcut: action.shortcut.str,
      action: action.callback
    }, title || action.title);
  }

  _export("ActionToMenuItem", ActionToMenuItem);

  return {
    setters: [function (_MenuItemJs) {
      MenuItem = _MenuItemJs.MenuItem;
    }, function (_utilsActionJs) {
      Action = _utilsActionJs.Action;
    }],
    execute: function () {
      ActionToMenuItem.propTypes = {
        action: PropTypes.instanceOf(Action),
        title: PropTypes.string
      };
    }
  };
});