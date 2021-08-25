System.register([], function (_export, _context) {
  "use strict";

  function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

  function MicroButton(props) {
    return /*#__PURE__*/React.createElement("div", _extends({
      className: "small-button " + props.type
    }, props.title ? {
      title: props.title
    } : {}, props.action ? {
      onClick: props.action
    } : {}), props.content);
  }

  _export("MicroButton", MicroButton);

  return {
    setters: [],
    execute: function () {
      MicroButton.propTypes = {
        title: PropTypes.string,
        action: PropTypes.func,
        type: PropTypes.string.isRequired,
        content: PropTypes.string.isRequired
      };
    }
  };
});