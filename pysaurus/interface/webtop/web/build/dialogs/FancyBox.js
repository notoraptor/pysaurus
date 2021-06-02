System.register([], function (_export, _context) {
  "use strict";

  var FancyBox;

  _export("FancyBox", void 0);

  return {
    setters: [],
    execute: function () {
      _export("FancyBox", FancyBox = class FancyBox extends React.Component {
        constructor(props) {
          // title
          // onClose()
          // onBuild? function(onClose)
          // children?
          super(props);
          this.callbackIndex = -1;
          this.checkShortcut = this.checkShortcut.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "fancybox-wrapper"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox-header horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox-title"
          }, this.props.title), /*#__PURE__*/React.createElement("div", {
            className: "fancybox-close"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.props.onClose
          }, "\xD7"))), /*#__PURE__*/React.createElement("div", {
            className: "fancybox-content"
          }, this.props.onBuild ? this.props.onBuild(this.props.onClose) : this.props.children)));
        }

        componentDidMount() {
          this.callbackIndex = KEYBOARD_MANAGER.register(this.checkShortcut);
        }

        componentWillUnmount() {
          KEYBOARD_MANAGER.unregister(this.callbackIndex);
        }
        /**
         * @param event {KeyboardEvent}
         */


        checkShortcut(event) {
          if (event.key === "Escape") {
            this.props.onClose();
            return true;
          }
        }

      });
    }
  };
});