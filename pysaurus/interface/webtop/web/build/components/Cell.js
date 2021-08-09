System.register([], function (_export, _context) {
  "use strict";

  var Cell;

  _export("Cell", void 0);

  return {
    setters: [],
    execute: function () {
      _export("Cell", Cell = class Cell extends React.Component {
        // className? str
        // center? bool
        // full? bool
        render() {
          const classNames = ['cell-wrapper'];
          if (this.props.className) classNames.push(this.props.className);

          if (this.props.center) {
            classNames.push('cell-center');
            classNames.push('horizontal');
          }

          if (this.props.full) classNames.push('cell-full');
          return /*#__PURE__*/React.createElement("div", {
            className: classNames.join(' ')
          }, /*#__PURE__*/React.createElement("div", {
            className: "cell"
          }, this.props.children));
        }

      });

      Cell.propTypes = {
        className: PropTypes.string,
        center: PropTypes.bool,
        full: PropTypes.bool
      };
    }
  };
});