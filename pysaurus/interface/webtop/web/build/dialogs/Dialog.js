System.register(["./FancyBox.js"], function (_export, _context) {
  "use strict";

  var FancyBox, Dialog;

  _export("Dialog", void 0);

  return {
    setters: [function (_FancyBoxJs) {
      FancyBox = _FancyBoxJs.FancyBox;
    }],
    execute: function () {
      _export("Dialog", Dialog = class Dialog extends React.Component {
        /**
         * @param props {{title: string, onClose: function?, yes: string?, no: string?}}
         */
        constructor(props) {
          // title: str
          // onClose: callback(bool)
          // yes? str
          // no? str
          super(props);
          this.yes = this.yes.bind(this);
          this.no = this.no.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(FancyBox, {
            title: this.props.title
          }, /*#__PURE__*/React.createElement("div", {
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
          }, this.props.no || "cancel")))));
        }

        yes() {
          Fancybox.onClose();
          if (this.props.onClose) this.props.onClose(true);
        }

        no() {
          Fancybox.onClose();
          if (this.props.onClose) this.props.onClose(false);
        }

      });
    }
  };
});