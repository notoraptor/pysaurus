System.register([], function (_export, _context) {
  "use strict";

  var MenuPack, MenuItem, MenuItemCheck, Menu;

  _export({
    MenuPack: void 0,
    MenuItem: void 0,
    MenuItemCheck: void 0,
    Menu: void 0
  });

  return {
    setters: [],
    execute: function () {
      _export("MenuPack", MenuPack = class MenuPack extends React.Component {
        constructor(props) {
          // title: str
          super(props);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "menu-pack"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title",
            onClick: this.showMenu
          }, /*#__PURE__*/React.createElement("div", {
            className: "text"
          }, this.props.title)), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.children));
        }

      });

      _export("MenuItem", MenuItem = class MenuItem extends React.Component {
        constructor(props) {
          // className? str
          // shortcut? str
          // action? function()
          super(props);
          this.onClick = this.onClick.bind(this);
        }

        render() {
          const classNames = ["menu-item horizontal"];
          if (this.props.className) classNames.push(this.props.className);
          return /*#__PURE__*/React.createElement("div", {
            className: classNames.join(' '),
            onClick: this.onClick
          }, /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }), /*#__PURE__*/React.createElement("div", {
            className: "text horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, this.props.children), /*#__PURE__*/React.createElement("div", {
            className: "shortcut"
          }, this.props.shortcut || '')));
        }

        onClick() {
          if (this.props.action) this.props.action();
        }

      });

      _export("MenuItemCheck", MenuItemCheck = class MenuItemCheck extends React.Component {
        constructor(props) {
          // action? function(checked)
          // checked? bool
          super(props);
          this.onClick = this.onClick.bind(this);
        }

        render() {
          const checked = !!this.props.checked;
          return /*#__PURE__*/React.createElement("div", {
            className: "menu-item horizontal",
            onClick: this.onClick
          }, /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, /*#__PURE__*/React.createElement("div", {
            className: "border"
          }, /*#__PURE__*/React.createElement("div", {
            className: 'check ' + (checked ? 'checked' : 'not-checked')
          }))), /*#__PURE__*/React.createElement("div", {
            className: "text"
          }, this.props.children));
        }

        onClick() {
          const checked = !this.props.checked;
          if (this.props.action) this.props.action(checked);
        }

      });

      _export("Menu", Menu = class Menu extends React.Component {
        constructor(props) {
          // title: str
          super(props);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "menu"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "text"
          }, this.props.title), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, "\u25B6")), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.children));
        }

      });
    }
  };
});