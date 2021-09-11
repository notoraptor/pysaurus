System.register([], function (_export, _context) {
  "use strict";

  function Menu(props) {
    return /*#__PURE__*/React.createElement("div", {
      className: "menu position-relative"
    }, /*#__PURE__*/React.createElement("div", {
      className: "title horizontal"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text"
    }, props.title), /*#__PURE__*/React.createElement("div", {
      className: "icon"
    }, "\u25B6")), /*#__PURE__*/React.createElement("div", {
      className: "content"
    }, props.children));
  }

  _export("Menu", Menu);

  return {
    setters: [],
    execute: function () {
      Menu.propTypes = {
        title: PropTypes.string.isRequired
      };
    }
  };
});