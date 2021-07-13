System.register([], function (_export, _context) {
  "use strict";

  var FancyBox;

  _export("FancyBox", void 0);

  return {
    setters: [],
    execute: function () {
      _export("FancyBox", FancyBox = class FancyBox extends React.Component {
        /**
         * @param props {{title: str}}
         */
        constructor(props) {
          // title
          // children
          super(props);
          this.callbackIndex = -1;
          this.checkShortcut = this.checkShortcut.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "fancybox-wrapper absolute-plain"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox vertical"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox-header horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox-title"
          }, this.props.title), /*#__PURE__*/React.createElement("div", {
            className: "fancybox-close"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: Fancybox.close
          }, "\xD7"))), /*#__PURE__*/React.createElement("div", {
            className: "fancybox-content"
          }, this.props.children)));
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
            Fancybox.close();
            return true;
          }
        }

      });
    }
  };
});