System.register(["./FancyBox.js", "../language.js", "../utils/FancyboxManager.js"], function (_export, _context) {
  "use strict";

  var FancyBox, LangContext, tr, Fancybox, Dialog;

  _export("Dialog", void 0);

  return {
    setters: [function (_FancyBoxJs) {
      FancyBox = _FancyBoxJs.FancyBox;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
      tr = _languageJs.tr;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }],
    execute: function () {
      _export("Dialog", Dialog = class Dialog extends React.Component {
        constructor(props) {
          super(props);
          this.yes = this.yes.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(FancyBox, {
            title: this.props.title
          }, /*#__PURE__*/React.createElement("div", {
            className: "dialog absolute-plain vertical"
          }, /*#__PURE__*/React.createElement("div", {
            className: "position-relative flex-grow-1 overflow-auto p-2 vertical"
          }, this.props.children), /*#__PURE__*/React.createElement("div", {
            className: "buttons flex-shrink-0 horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "button flex-grow-1 p-2 yes"
          }, /*#__PURE__*/React.createElement("button", {
            className: "block bold",
            onClick: this.yes
          }, this.props.yes || tr("yes"))), /*#__PURE__*/React.createElement("div", {
            className: "button flex-grow-1 p-2 no"
          }, /*#__PURE__*/React.createElement("button", {
            className: "block bold",
            onClick: Fancybox.close
          }, this.props.no || tr("cancel"))))));
        }

        yes() {
          Fancybox.close();
          if (this.props.action) this.props.action();
        }

      });

      Dialog.contextType = LangContext;
      Dialog.propTypes = {
        title: PropTypes.string.isRequired,
        // action()
        action: PropTypes.func,
        yes: PropTypes.string,
        no: PropTypes.string
      };
    }
  };
});