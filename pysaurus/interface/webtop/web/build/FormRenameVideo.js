System.register(["./Dialog.js"], function (_export, _context) {
  "use strict";

  var Dialog, FormRenameVideo;

  _export("FormRenameVideo", void 0);

  return {
    setters: [function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }],
    execute: function () {
      _export("FormRenameVideo", FormRenameVideo = class FormRenameVideo extends React.Component {
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
            yes: "rename",
            no: "cancel",
            onClose: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-rename-video"
          }, /*#__PURE__*/React.createElement("h1", null, "Rename"), /*#__PURE__*/React.createElement("h2", null, /*#__PURE__*/React.createElement("code", {
            id: "filename"
          }, this.props.filename)), /*#__PURE__*/React.createElement("p", {
            className: "form"
          }, /*#__PURE__*/React.createElement("input", {
            type: "text",
            name: "name",
            id: "name",
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

        onClose(yes) {
          this.submit(yes);
        }

        onKeyDown(event) {
          if (event.key === "Enter") {
            this.submit(true);
          }
        }

        submit(yes) {
          let title = null;

          if (yes) {
            title = this.state.title;
            if (!title.length || title === this.props.title) title = null;
          }

          this.props.onClose(title);
        }

      });
    }
  };
});