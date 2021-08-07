System.register([], function (_export, _context) {
  "use strict";

  var MenuPack;

  _export("MenuPack", void 0);

  return {
    setters: [],
    execute: function () {
      _export("MenuPack", MenuPack = class MenuPack extends React.Component {
        constructor(props) {
          // title: str
          super(props);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "menu-pack"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, /*#__PURE__*/React.createElement("div", {
            className: "text"
          }, this.props.title)), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.children));
        }

      });

      MenuPack.propTypes = {
        title: PropTypes.string.isRequired
      };
    }
  };
});