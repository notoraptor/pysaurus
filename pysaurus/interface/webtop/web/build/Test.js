System.register(["./buttons.js", "./MenuPack.js", "./constants.js", "./SetInput.js", "./Dialog.js"], function (_export, _context) {
  "use strict";

  var Cross, SettingIcon, Menu, MenuItem, MenuItemCheck, MenuPack, PAGE_SIZES, SetInput, ComponentController, Dialog, Test;

  _export("Test", void 0);

  return {
    setters: [function (_buttonsJs) {
      Cross = _buttonsJs.Cross;
      SettingIcon = _buttonsJs.SettingIcon;
    }, function (_MenuPackJs) {
      Menu = _MenuPackJs.Menu;
      MenuItem = _MenuPackJs.MenuItem;
      MenuItemCheck = _MenuPackJs.MenuItemCheck;
      MenuPack = _MenuPackJs.MenuPack;
    }, function (_constantsJs) {
      PAGE_SIZES = _constantsJs.PAGE_SIZES;
    }, function (_SetInputJs) {
      SetInput = _SetInputJs.SetInput;
      ComponentController = _SetInputJs.ComponentController;
    }, function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }],
    execute: function () {
      _export("Test", Test = class Test extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            pageSize: PAGE_SIZES[0],
            confirmDeletion: false,
            arr: ['a', 'b', 'ccc']
          };
        }

        render() {
          const c = new ComponentController(this, 'arr');
          return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SetInput, {
            identifier: "entry",
            controller: c,
            values: ['my', 'name', 'is', 'Emninem']
          }), /*#__PURE__*/React.createElement(MenuPack, {
            title: "Options"
          }, /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: "Ctrl+S",
            action: () => console.log('select videos')
          }, "Select videos ..."), /*#__PURE__*/React.createElement(MenuItem, {
            action: () => console.log('reload database')
          }, "Reload database ..."), /*#__PURE__*/React.createElement(MenuItem, {
            action: () => console.log('manage properties')
          }, "Manage properties"), /*#__PURE__*/React.createElement(Menu, {
            title: "Page size ..."
          }, /*#__PURE__*/React.createElement(Menu, {
            title: "again"
          }, /*#__PURE__*/React.createElement(MenuItem, null, "a"), /*#__PURE__*/React.createElement(MenuItem, null, "b"), /*#__PURE__*/React.createElement(MenuItem, null, "c")), PAGE_SIZES.map((count, index) => /*#__PURE__*/React.createElement(MenuItemCheck, {
            key: index,
            checked: this.state.pageSize === count,
            action: checked => {
              if (checked) this.setState({
                pageSize: count
              });
            }
          }, count, " video", count > 1 ? 's' : '', " per page"))), /*#__PURE__*/React.createElement(MenuItemCheck, {
            checked: this.state.confirmDeletion,
            action: checked => this.setState({
              confirmDeletion: checked
            })
          }, "confirm deletion for entries not found")), "Hello! ", /*#__PURE__*/React.createElement(Cross, {
            action: () => console.log('cross!')
          }), /*#__PURE__*/React.createElement("a", {
            href: "https://google.fr"
          }, "yayayayayaya!"), /*#__PURE__*/React.createElement("input", {
            type: "text"
          }), "Hello! ", /*#__PURE__*/React.createElement("button", {
            onClick: () => this.fancy()
          }, "click here!"));
        }

        fancy() {
          this.props.app.loadDialog("Test fancy box!", onClose => /*#__PURE__*/React.createElement(Dialog, {
            onClose: yes => {
              onClose();
              console.log(`Choice: ${yes ? 'yes' : 'no'}`);
            }
          }, /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world")));
        }

      });
    }
  };
});