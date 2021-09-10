System.register(["../dialogs/Dialog.js"], function (_export, _context) {
  "use strict";

  var Dialog, FormVideoRename;

  _export("FormVideoRename", void 0);

  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }],
    execute: function () {
      _export("FormVideoRename", FormVideoRename = class FormVideoRename extends React.Component {
        constructor(props) {
          // filename: str
          // title: str
          // onClose(newTitle)
          super(props);
          this.state = {
            title: this.props.title
          };
          this.onChange = this.onChange.bind(this);
          this.onClose = this.onClose.bind(this);
          this.onKeyDown = this.onKeyDown.bind(this);
          this.submit = this.submit.bind(this);
          this.onFocusInput = this.onFocusInput.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            title: "Rename",
            yes: "rename",
            action: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-rename text-center"
          }, /*#__PURE__*/React.createElement("h1", null, "Rename video"), /*#__PURE__*/React.createElement("h2", null, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, this.props.filename)), /*#__PURE__*/React.createElement("p", {
            className: "form"
          }, /*#__PURE__*/React.createElement("input", {
            type: "text",
            id: "name",
            className: "block",
            value: this.state.title,
            onChange: this.onChange,
            onKeyDown: this.onKeyDown,
            onFocus: this.onFocusInput
          }))));
        }

        componentDidMount() {
          document.querySelector('input#name').focus();
        }

        onFocusInput(event) {
          event.target.select();
        }

        onChange(event) {
          this.setState({
            title: event.target.value
          });
        }

        onClose() {
          this.submit();
        }

        onKeyDown(event) {
          if (event.key === "Enter") {
            Fancybox.close();
            this.submit();
          }
        }

        submit(yes) {
          if (this.state.title && this.state.title !== this.props.title) this.props.onClose(this.state.title);
        }

      });
    }
  };
});