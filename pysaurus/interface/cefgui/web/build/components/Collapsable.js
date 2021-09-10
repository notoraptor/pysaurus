System.register(["../utils/constants.js"], function (_export, _context) {
  "use strict";

  var Characters, Collapsable;

  _export("Collapsable", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
    }],
    execute: function () {
      _export("Collapsable", Collapsable = class Collapsable extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            stack: false
          };
          this.stack = this.stack.bind(this);
        }

        render() {
          const lite = this.props.lite !== undefined ? this.props.lite : true;
          return /*#__PURE__*/React.createElement("div", {
            className: `abstract-collapsable ${lite ? "collapsable" : "stack"} ${this.props.className || ''}`
          }, /*#__PURE__*/React.createElement("div", {
            className: "header clickable horizontal",
            onClick: this.stack
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, this.props.title), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, this.state.stack ? Characters.ARROW_DOWN : Characters.ARROW_UP)), this.state.stack ? '' : /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.children));
        }

        stack() {
          this.setState({
            stack: !this.state.stack
          });
        }

      });

      Collapsable.propTypes = {
        title: PropTypes.string,
        className: PropTypes.string,
        lite: PropTypes.bool
      };
    }
  };
});