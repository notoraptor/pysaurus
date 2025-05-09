System.register(["../BaseComponent.js", "../utils/FancyboxManager.js"], function (_export, _context) {
  "use strict";

  var BaseComponent, Fancybox, FancyBox;
  _export("FancyBox", void 0);
  return {
    setters: [function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }],
    execute: function () {
      _export("FancyBox", FancyBox = class FancyBox extends BaseComponent {
        /**
         * @param props {{title: str}}
         */
        constructor(props) {
          // title, onClose() ?, children
          super(props);
          this.callbackIndex = -1;
        }
        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "fancybox-wrapper absolute-plain"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox vertical"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox-header flex-shrink-0 horizontal p-2"
          }, /*#__PURE__*/React.createElement("div", {
            className: "fancybox-title flex-grow-1 text-center",
            title: this.props.title
          }, /*#__PURE__*/React.createElement("strong", null, this.props.title)), /*#__PURE__*/React.createElement("div", {
            className: "pl-2"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.onClose
          }, "\xD7"))), /*#__PURE__*/React.createElement("div", {
            className: "fancybox-content position-relative overflow-auto flex-grow-1 p-2"
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
            this.onClose();
            return true;
          }
        }
        onClose() {
          if (!this.props.onClose || this.props.onClose()) Fancybox.close();
        }
      });
      FancyBox.propTypes = {
        title: PropTypes.string.isRequired,
        // onClose()
        onClose: PropTypes.func
      };
    }
  };
});