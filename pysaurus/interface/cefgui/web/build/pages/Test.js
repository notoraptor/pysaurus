System.register(["../components/MenuPack.js", "../utils/constants.js", "../components/SetInput.js", "../dialogs/Dialog.js", "../components/Cross.js", "../dialogs/FancyBox.js", "./HomePage.js", "../utils/backend.js"], function (_export, _context) {
  "use strict";

  var MenuPack, PAGE_SIZES, ComponentController, SetInput, Dialog, Cross, FancyBox, HomePage, python_call, Test;

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
    }, function (_dialogsFancyBoxJs) {
      FancyBox = _dialogsFancyBoxJs.FancyBox;
    }, function (_HomePageJs) {
      HomePage = _HomePageJs.HomePage;
    }, function (_utilsBackendJs) {
      python_call = _utilsBackendJs.python_call;
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
          }), "Hello! ", /*#__PURE__*/React.createElement(Cross, {
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
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: "Test Fancy Box 2!",
            action: () => console.log(`Choice: yes!`)
          }, /*#__PURE__*/React.createElement("h1", null, "hello world ", this.state.pageSize), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world")));
        }

      });
    }
  };
});