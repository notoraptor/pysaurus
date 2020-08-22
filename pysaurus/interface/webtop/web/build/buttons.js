System.register([], function (_export, _context) {
  "use strict";

  var Cross, SettingIcon;

  function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

  _export({
    Cross: void 0,
    SettingIcon: void 0
  });

  return {
    setters: [],
    execute: function () {
      _export("Cross", Cross = class Cross extends React.Component {
        constructor(props) {
          // action ? function()
          // title? str
          super(props);
          this.type = "cross";
          this.content = Utils.CHARACTER_CROSS;
        }

        render() {
          return /*#__PURE__*/React.createElement("div", _extends({
            className: "small-button " + this.type
          }, this.props.title ? {
            title: this.props.title
          } : {}, this.props.action ? {
            onClick: this.props.action
          } : {}), /*#__PURE__*/React.createElement("span", {
            className: "content"
          }, this.content));
        }

      });

      _export("SettingIcon", SettingIcon = class SettingIcon extends Cross {
        constructor(props) {
          // action ? function()
          // title? str
          super(props);
          this.type = "settings";
          this.content = Utils.CHARACTER_SETTINGS;
        }

      });
    }
  };
});