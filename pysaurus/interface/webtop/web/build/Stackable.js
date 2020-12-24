System.register([], function (_export, _context) {
  "use strict";

  var Stackable;

  _export("Stackable", void 0);

  return {
    setters: [],
    execute: function () {
      _export("Stackable", Stackable = class Stackable extends React.Component {
        constructor(props) {
          // title: str
          // className: str
          // children ...
          super(props);
          this.state = {
            stack: false
          };
          this.stack = this.stack.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: `stack ${this.props.className || ''}`
          }, /*#__PURE__*/React.createElement("div", {
            className: "stack-title",
            onClick: this.stack
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, this.props.title), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, this.state.stack ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP)), this.state.stack ? '' : /*#__PURE__*/React.createElement("div", {
            className: "stack-content"
          }, this.props.children));
        }

        stack() {
          this.setState({
            stack: !this.state.stack
          });
        }

      });
    }
  };
});