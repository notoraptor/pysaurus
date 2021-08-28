System.register(["../components/SetInput.js", "../dialogs/Dialog.js", "../utils/functions.js"], function (_export, _context) {
  "use strict";

  var ComponentController, SetInput, Dialog, parsePropValString, FormVideoEditProperties;

  _export("FormVideoEditProperties", void 0);

  return {
    setters: [function (_componentsSetInputJs) {
      ComponentController = _componentsSetInputJs.ComponentController;
      SetInput = _componentsSetInputJs.SetInput;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_utilsFunctionsJs) {
      parsePropValString = _utilsFunctionsJs.parsePropValString;
    }],
    execute: function () {
      _export("FormVideoEditProperties", FormVideoEditProperties = class FormVideoEditProperties extends React.Component {
        constructor(props) {
          // data
          // definitions
          // onClose
          super(props);
          this.state = {};
          const properties = this.props.data.properties;

          for (let def of this.props.definitions) {
            const name = def.name;
            this.state[name] = properties.hasOwnProperty(name) ? properties[name] : def.defaultValue;
          }

          this.onClose = this.onClose.bind(this);
          this.onChange = this.onChange.bind(this);
        }

        render() {
          const data = this.props.data;
          const hasThumbnail = data.has_thumbnail;
          return /*#__PURE__*/React.createElement(Dialog, {
            title: 'Edit video properties',
            yes: "save",
            action: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-set-properties horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "info"
          }, /*#__PURE__*/React.createElement("div", {
            className: "image"
          }, hasThumbnail ? /*#__PURE__*/React.createElement("img", {
            alt: data.title,
            src: data.thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, "no thumbnail")), /*#__PURE__*/React.createElement("div", {
            className: "filename mb-1"
          }, /*#__PURE__*/React.createElement("code", null, data.filename)), data.title === data.file_title ? '' : /*#__PURE__*/React.createElement("div", {
            className: "title mb-1"
          }, /*#__PURE__*/React.createElement("em", null, data.title))), /*#__PURE__*/React.createElement("div", {
            className: "properties"
          }, /*#__PURE__*/React.createElement("table", {
            className: "first-td-text-right"
          }, this.props.definitions.map((def, index) => {
            const name = def.name;
            let input;

            if (def.multiple) {
              let possibleValues = null;
              if (def.enumeration) possibleValues = def.enumeration;else if (def.type === "bool") possibleValues = [false, true];
              const controller = new ComponentController(this, name, value => parsePropValString(def.type, possibleValues, value));
              input = /*#__PURE__*/React.createElement(SetInput, {
                controller: controller,
                values: possibleValues
              });
            } else if (def.enumeration) {
              input = /*#__PURE__*/React.createElement("select", {
                value: this.state[name],
                onChange: event => this.onChange(event, def)
              }, def.enumeration.map((value, valueIndex) => /*#__PURE__*/React.createElement("option", {
                key: valueIndex,
                value: value
              }, value)));
            } else if (def.type === "bool") {
              input = /*#__PURE__*/React.createElement("select", {
                value: this.state[name],
                onChange: event => this.onChange(event, def)
              }, /*#__PURE__*/React.createElement("option", {
                value: "false"
              }, "false"), /*#__PURE__*/React.createElement("option", {
                value: "true"
              }, "true"));
            } else {
              input = /*#__PURE__*/React.createElement("input", {
                type: def.type === "int" ? "number" : "text",
                onChange: event => this.onChange(event, def),
                value: this.state[name]
              });
            }

            return /*#__PURE__*/React.createElement("tr", {
              key: index
            }, /*#__PURE__*/React.createElement("td", {
              className: "label"
            }, /*#__PURE__*/React.createElement("strong", null, name)), /*#__PURE__*/React.createElement("td", {
              className: "input"
            }, input));
          })))));
        }

        onClose() {
          this.props.onClose(this.state);
        }

        onChange(event, def) {
          try {
            this.setState({
              [def.name]: parsePropValString(def.type, def.enumeration, event.target.value)
            });
          } catch (exception) {
            window.alert(exception.toString());
          }
        }

      });
    }
  };
});