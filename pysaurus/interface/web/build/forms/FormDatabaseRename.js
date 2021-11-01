System.register(["../dialogs/Dialog.js", "../language.js"], function (_export, _context) {
  "use strict";

  var Dialog, LangContext, FormDatabaseRename;

  _export("FormDatabaseRename", void 0);

  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
    }],
    execute: function () {
      _export("FormDatabaseRename", FormDatabaseRename = class FormDatabaseRename extends React.Component {
        constructor(props) {
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
            title: this.context.form_title_rename_database.format({
              name: this.props.title
            }),
            yes: this.context.text_rename,
            action: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-rename text-center"
          }, /*#__PURE__*/React.createElement("h1", null, this.context.text_rename_database), /*#__PURE__*/React.createElement("h2", null, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, this.props.title)), /*#__PURE__*/React.createElement("p", {
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

        submit() {
          if (this.state.title && this.state.title !== this.props.title) this.props.onClose(this.state.title);
        }

      });

      FormDatabaseRename.contextType = LangContext;
    }
  };
});