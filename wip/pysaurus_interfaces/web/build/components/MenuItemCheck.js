System.register([], function (_export, _context) {
  "use strict";

  var MenuItemCheck;
  _export("MenuItemCheck", void 0);
  return {
    setters: [],
    execute: function () {
      _export("MenuItemCheck", MenuItemCheck = class MenuItemCheck extends React.Component {
        constructor(props) {
          // action? function(checked)
          // checked? bool
          super(props);
          this.onClick = this.onClick.bind(this);
        }
        render() {
          const checked = !!this.props.checked;
          return /*#__PURE__*/React.createElement("div", {
            className: "menu-item horizontal",
            onClick: this.onClick
          }, /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, /*#__PURE__*/React.createElement("div", {
            className: "border"
          }, /*#__PURE__*/React.createElement("div", {
            className: "check " + (checked ? "checked" : "not-checked")
          }))), /*#__PURE__*/React.createElement("div", {
            className: "text"
          }, this.props.children));
        }
        onClick() {
          const checked = !this.props.checked;
          if (this.props.action) this.props.action(checked);
        }
      });
    }
  };
});