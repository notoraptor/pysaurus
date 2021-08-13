System.register(["./MenuItem.js"], function (_export, _context) {
  "use strict";

  var MenuItem;

  /**
   * @param props {{action: Action, title: str?}}
   */
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
    }],
    execute: function () {}
  };
});