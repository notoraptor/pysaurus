System.register(["../dialogs/Dialog.js", "../language.js", "../utils/FancyboxManager.js", "../BaseComponent.js"], function (_export, _context) {
  "use strict";

  var Dialog, tr, Fancybox, BaseComponent, GenericFormRename;
  _export("GenericFormRename", void 0);
  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_languageJs) {
      tr = _languageJs.tr;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }, function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }],
    execute: function () {
      _export("GenericFormRename", GenericFormRename = class GenericFormRename extends BaseComponent {
        getInitialState() {
          return {
            data: this.props.data
          };
        }
        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            title: this.props.title,
            yes: tr("rename"),
            action: this.submit
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-rename text-center"
          }, /*#__PURE__*/React.createElement("h1", null, this.props.header), /*#__PURE__*/React.createElement("h2", null, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, this.props.description)), /*#__PURE__*/React.createElement("p", {
            className: "form"
          }, /*#__PURE__*/React.createElement("input", {
            type: "text",
            id: "name",
            className: "block",
            value: this.state.data,
            onChange: this.onChange,
            onKeyDown: this.onKeyDown,
            onFocus: this.onFocusInput
          }))));
        }
        componentDidMount() {
          document.querySelector("input#name").focus();
        }
        onFocusInput(event) {
          event.target.select();
        }
        onChange(event) {
          this.setState({
            data: event.target.value
          });
        }
        onKeyDown(event) {
          if (event.key === "Enter") {
            Fancybox.close();
            this.submit();
          }
        }
        submit() {
          if (this.state.data && this.state.data !== this.props.data) this.props.onClose(this.state.data);
        }
      });
      GenericFormRename.propTypes = {
        title: PropTypes.string.isRequired,
        header: PropTypes.string.isRequired,
        description: PropTypes.string.isRequired,
        data: PropTypes.string.isRequired,
        onClose: PropTypes.func.isRequired
      };
    }
  };
});