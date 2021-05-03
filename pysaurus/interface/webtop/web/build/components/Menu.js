System.register([], function (_export, _context) {
  "use strict";

  var Menu;

  _export("Menu", void 0);

  return {
    setters: [],
    execute: function () {
      _export("Menu", Menu = class Menu extends React.Component {
        constructor(props) {
          // title: str
          super(props);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "menu"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "text"
          }, this.props.title), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, "\u25B6")), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.children));
        }

      });
    }
  };
});