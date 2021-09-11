System.register([], function (_export, _context) {
  "use strict";

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
    execute: function () {
      MenuItemRadio.propTypes = {
        value: PropTypes.object,
        checked: PropTypes.bool,
        // action(value)
        action: PropTypes.func
      };
    }
  };
});