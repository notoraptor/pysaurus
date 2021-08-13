System.register([], function (_export, _context) {
  "use strict";

  var MenuItem;

  _export("MenuItem", void 0);

  return {
    setters: [],
    execute: function () {
      _export("MenuItem", MenuItem = class MenuItem extends React.Component {
        constructor(props) {
          // className? str
          // shortcut? str
          // action? function()
          super(props);
          this.onClick = this.onClick.bind(this);
        }

        render() {
          const classNames = ["menu-item horizontal"];
          if (this.props.className) classNames.push(this.props.className);
          return /*#__PURE__*/React.createElement("div", {
            className: classNames.join(' '),
            onClick: this.onClick
          }, /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }), /*#__PURE__*/React.createElement("div", {
            className: "text horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, this.props.children), /*#__PURE__*/React.createElement("div", {
            className: "shortcut"
          }, this.props.shortcut || '')));
        }

        onClick() {
          if (this.props.action) this.props.action();
        }

      });

      MenuItem.propTypes = {
        className: PropTypes.string,
        shortcut: PropTypes.string,
        action: PropTypes.func.isRequired // action()

      };
    }
  };
});