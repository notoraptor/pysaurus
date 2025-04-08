System.register(["../components/Cell.js", "../dialogs/Dialog.js", "../utils/FancyboxManager.js", "../BaseComponent.js"], function (_export, _context) {
  "use strict";

  var Cell, Dialog, Fancybox, BaseComponent, FormPaginationGoTo;
  _export("FormPaginationGoTo", void 0);
  return {
    setters: [function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }, function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }],
    execute: function () {
      _export("FormPaginationGoTo", FormPaginationGoTo = class FormPaginationGoTo extends BaseComponent {
        // nbPages
        // pageNumber
        // onClose(pageNumber)

        getInitialState() {
          return {
            pageNumber: this.props.pageNumber
          };
        }
        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            title: "Go to page:",
            yes: "go",
            action: this.onClose
          }, /*#__PURE__*/React.createElement(Cell, {
            center: true,
            full: true,
            className: "text-center"
          }, /*#__PURE__*/React.createElement("input", {
            type: "number",
            id: "input-go",
            min: 1,
            max: this.props.nbPages,
            step: 1,
            value: this.state.pageNumber + 1,
            onFocus: this.onFocusInput,
            onChange: this.onChange,
            onKeyDown: this.onInput
          }), " ", "/ ", this.props.nbPages));
        }
        componentDidMount() {
          document.querySelector("#input-go").focus();
        }
        onFocusInput(event) {
          event.target.select();
        }
        onChange(event) {
          const value = event.target.value;
          let pageNumber = (value || 1) - 1;
          if (pageNumber >= this.props.nbPages) pageNumber = this.props.nbPages - 1;
          if (pageNumber < 0) pageNumber = 0;
          this.setState({
            pageNumber
          });
        }
        onInput(event) {
          if (event.key === "Enter") {
            Fancybox.close();
            this.props.onClose(this.state.pageNumber);
          }
        }
        onClose() {
          this.props.onClose(this.state.pageNumber);
        }
      });
    }
  };
});