System.register(["../components/MenuPack.js", "../utils/constants.js", "../components/SetInput.js", "../dialogs/Dialog.js", "../components/Cross.js", "../components/MenuItem.js", "../components/MenuItemCheck.js", "../components/Menu.js", "../dialogs/FancyBox.js"], function (_export, _context) {
  "use strict";

  var MenuPack, PAGE_SIZES, ComponentController, SetInput, Dialog, Cross, MenuItem, MenuItemCheck, Menu, FancyBox, Test;

  _export("Test", void 0);

  return {
    setters: [function (_componentsMenuPackJs) {
      MenuPack = _componentsMenuPackJs.MenuPack;
    }, function (_utilsConstantsJs) {
      PAGE_SIZES = _utilsConstantsJs.PAGE_SIZES;
    }, function (_componentsSetInputJs) {
      ComponentController = _componentsSetInputJs.ComponentController;
      SetInput = _componentsSetInputJs.SetInput;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_componentsCrossJs) {
      Cross = _componentsCrossJs.Cross;
    }, function (_componentsMenuItemJs) {
      MenuItem = _componentsMenuItemJs.MenuItem;
    }, function (_componentsMenuItemCheckJs) {
      MenuItemCheck = _componentsMenuItemCheckJs.MenuItemCheck;
    }, function (_componentsMenuJs) {
      Menu = _componentsMenuJs.Menu;
    }, function (_dialogsFancyBoxJs) {
      FancyBox = _dialogsFancyBoxJs.FancyBox;
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
            onClick: () => this.fancy2()
          }, "click here!"));
        }

        fancy2() {
          Fancybox.load( /*#__PURE__*/React.createElement(FancyBox, {
            title: "Test Fancy Box 2!",
            onClose: Fancybox.onClose
          }, /*#__PURE__*/React.createElement(Dialog, {
            onClose: yes => {
              Fancybox.onClose();
              console.log(`Choice: ${yes ? 'yes' : 'no'}`);
            }
          }, /*#__PURE__*/React.createElement("h1", null, "hello world ", this.state.pageSize), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"))));
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