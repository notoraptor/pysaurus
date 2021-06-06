System.register(["../dialogs/Dialog.js", "../components/Cell.js"], function (_export, _context) {
  "use strict";

  var Dialog, Cell, FormGoToPage;

  _export("FormGoToPage", void 0);

  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }],
    execute: function () {
      _export("FormGoToPage", FormGoToPage = class FormGoToPage extends React.Component {
        constructor(props) {
          // nbPages
          // pageNumber
          // onClose(pageNumber)
          super(props);
          this.state = {
            pageNumber: this.props.pageNumber
          };
          this.onFocusInput = this.onFocusInput.bind(this);
          this.onChange = this.onChange.bind(this);
          this.onInput = this.onInput.bind(this);
          this.onClose = this.onClose.bind(this);
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
          }), " / ", this.props.nbPages));
        }

        componentDidMount() {
          document.querySelector('#input-go').focus();
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