System.register([], function (_export, _context) {
  "use strict";

  /**
   * @callback MenuItemRadioCallback
   * @param {Object} value
   */

  /**
   * @param props {{value: Object, checked: boolean, action: MenuItemRadioCallback, children: Object}}
   */
  function MenuItemRadio(props) {
    return /*#__PURE__*/React.createElement("div", {
      className: "menu-item radio horizontal",
      onClick: () => props.action(props.value)
    }, /*#__PURE__*/React.createElement("div", {
      className: "icon"
    }, /*#__PURE__*/React.createElement("div", {
      className: "border"
    }, /*#__PURE__*/React.createElement("div", {
      className: 'check ' + (!!props.checked ? 'checked' : 'not-checked')
    }))), /*#__PURE__*/React.createElement("div", {
      className: "text"
    }, props.children));
  }

  _export("MenuItemRadio", MenuItemRadio);

  return {
    setters: [],
    execute: function () {}
  };
});