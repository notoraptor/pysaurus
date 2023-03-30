System.register([], function (_export, _context) {
  "use strict";

  function MenuPack(props) {
    return /*#__PURE__*/React.createElement("div", {
      className: "menu-pack clickable position-relative"
    }, /*#__PURE__*/React.createElement("div", {
      className: "title"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text"
    }, props.title)), /*#__PURE__*/React.createElement("div", {
      className: "content"
    }, props.children));
  }
  _export("MenuPack", MenuPack);
  return {
    setters: [],
    execute: function () {
      MenuPack.propTypes = {
        title: PropTypes.string.isRequired
      };
    }
  };
});