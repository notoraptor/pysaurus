System.register([], function (_export, _context) {
  "use strict";

  function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
  function MicroButton(props) {
    return /*#__PURE__*/React.createElement("div", _extends({
      className: "small-button clickable bold text-center " + props.type
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