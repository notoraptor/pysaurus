System.register([], function (_export, _context) {
  "use strict";

  var Collapsable;

  _export("Collapsable", void 0);

  return {
    setters: [],
    execute: function () {
      _export("Collapsable", Collapsable = class Collapsable extends React.Component {
        constructor(props) {
          // title: str
          // className? str
          // children ...
          // lite? bool = true
          super(props);
          this.state = {
            stack: false
          };
          this.stack = this.stack.bind(this);
        }

        render() {
          const lite = this.props.lite !== undefined ? this.props.lite : true;
          return /*#__PURE__*/React.createElement("div", {
            className: `${lite ? "collapsable" : "stack"} ${this.props.className || {}}`
          }, /*#__PURE__*/React.createElement("div", {
            className: "header horizontal",
            onClick: this.stack
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, this.props.title), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, this.state.stack ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP)), this.state.stack ? '' : /*#__PURE__*/React.createElement("div", {
            className: "content"
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