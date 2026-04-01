System.register(["../utils/Action.js", "./MenuItem.js"], function (_export, _context) {
  "use strict";

  var Action, MenuItem;
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
    setters: [function (_utilsActionJs) {
      Action = _utilsActionJs.Action;
    }, function (_MenuItemJs) {
      MenuItem = _MenuItemJs.MenuItem;
    }],
    execute: function () {
      ActionToMenuItem.propTypes = {
        action: PropTypes.instanceOf(Action).isRequired,
        title: PropTypes.string
      };
    }
  };
});