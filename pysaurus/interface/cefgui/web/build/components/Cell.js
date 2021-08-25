System.register([], function (_export, _context) {
  "use strict";

  function Cell(props) {
    const classNames = ['cell-wrapper'];
    if (props.className) classNames.push(props.className);

    if (props.center) {
      classNames.push('cell-center');
      classNames.push('horizontal');
    }

    if (props.full) classNames.push('cell-full');
    return /*#__PURE__*/React.createElement("div", {
      className: classNames.join(' ')
    }, /*#__PURE__*/React.createElement("div", {
      className: "cell"
    }, props.children));
  }

  _export("Cell", Cell);

  return {
    setters: [],
    execute: function () {
      Cell.propTypes = {
        className: PropTypes.string,
        center: PropTypes.bool,
        full: PropTypes.bool
      };
    }
  };
});