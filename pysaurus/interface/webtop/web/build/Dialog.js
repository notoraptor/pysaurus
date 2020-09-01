System.register([], function (_export, _context) {
  "use strict";

  var Dialog;

  _export("Dialog", void 0);

  return {
    setters: [],
    execute: function () {
      _export("Dialog", Dialog = class Dialog extends React.Component {
        constructor(props) {
          // onClose: callback(bool)
          // yes? str
          // no? str
          super(props);
          this.yes = this.yes.bind(this);
          this.no = this.no.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "dialog"
          }, /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.children), /*#__PURE__*/React.createElement("div", {
            className: "buttons horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "button yes"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.yes
          }, this.props.yes || "yes")), /*#__PURE__*/React.createElement("div", {
            className: "button no"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.no
          }, this.props.no || "no"))));
        }

        yes() {
          this.props.onClose(true);
        }

        no() {
          this.props.onClose(false);
        }

      });
    }
  };
});