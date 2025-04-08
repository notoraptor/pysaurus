System.register(["../components/Cross.js", "../components/SetInput.js", "../dialogs/Dialog.js", "../utils/FancyboxManager.js", "../utils/constants.js", "../BaseComponent.js"], function (_export, _context) {
  "use strict";

  var Cross, ComponentController, SetInput, Dialog, Fancybox, PAGE_SIZES, BaseComponent, Test;
  _export("Test", void 0);
  return {
    setters: [function (_componentsCrossJs) {
      Cross = _componentsCrossJs.Cross;
    }, function (_componentsSetInputJs) {
      ComponentController = _componentsSetInputJs.ComponentController;
      SetInput = _componentsSetInputJs.SetInput;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }, function (_utilsConstantsJs) {
      PAGE_SIZES = _utilsConstantsJs.PAGE_SIZES;
    }, function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }],
    execute: function () {
      _export("Test", Test = class Test extends BaseComponent {
        getInitialState() {
          return {
            pageSize: PAGE_SIZES[0],
            confirmDeletion: false,
            arr: ["a", "b", "ccc"]
          };
        }
        render() {
          const c = new ComponentController(this, "arr");
          return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SetInput, {
            identifier: "entry",
            controller: c,
            values: ["my", "name", "is", "Emninem"]
          }), "Hello! ", /*#__PURE__*/React.createElement(Cross, {
            action: () => console.log("cross!")
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
            action: () => console.log("Choice: yes!")
          }, /*#__PURE__*/React.createElement("h1", null, "hello world ", this.state.pageSize), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world"), /*#__PURE__*/React.createElement("h1", null, "hello world")));
        }
      });
    }
  };
});