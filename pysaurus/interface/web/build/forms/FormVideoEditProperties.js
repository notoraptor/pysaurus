System.register(["../BaseComponent.js", "../components/SetInput.js", "../dialogs/Dialog.js", "../language.js", "../utils/functions.js"], function (_export, _context) {
  "use strict";

  var BaseComponent, ComponentPropController, SetInput, Dialog, tr, UTILITIES, FormVideoEditProperties;
  _export("FormVideoEditProperties", void 0);
  return {
    setters: [function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }, function (_componentsSetInputJs) {
      ComponentPropController = _componentsSetInputJs.ComponentPropController;
      SetInput = _componentsSetInputJs.SetInput;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_languageJs) {
      tr = _languageJs.tr;
    }, function (_utilsFunctionsJs) {
      UTILITIES = _utilsFunctionsJs.UTILITIES;
    }],
    execute: function () {
      _export("FormVideoEditProperties", FormVideoEditProperties = class FormVideoEditProperties extends BaseComponent {
        // data
        // definitions
        // onClose

        getInitialState() {
          let state = {};
          const properties = this.props.data.properties;
          for (let def of this.props.definitions) {
            const name = def.name;
            state[name] = properties.hasOwnProperty(name) ? properties[name] : def.defaultValues;
          }
          return state;
        }
        render() {
          const data = this.props.data;
          const hasThumbnail = data.with_thumbnails;
          return /*#__PURE__*/React.createElement(Dialog, {
            title: tr("Edit video properties"),
            yes: tr("save"),
            action: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-video-edit-properties horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "info"
          }, /*#__PURE__*/React.createElement("div", {
            className: "image"
          }, hasThumbnail ? /*#__PURE__*/React.createElement("img", {
            alt: data.title,
            src: data.thumbnail_path
          }) : /*#__PURE__*/React.createElement("div", {
            className: "no-thumbnail"
          }, tr("no thumbnail"))), /*#__PURE__*/React.createElement("div", {
            className: "filename p-1 mb-1"
          }, /*#__PURE__*/React.createElement("code", null, data.filename)), data.title === data.file_title ? "" : /*#__PURE__*/React.createElement("div", {
            className: "title mb-1"
          }, /*#__PURE__*/React.createElement("em", null, data.title))), /*#__PURE__*/React.createElement("div", {
            className: "properties flex-grow-1"
          }, /*#__PURE__*/React.createElement("table", {
            className: "first-td-text-right w-100"
          }, /*#__PURE__*/React.createElement("tbody", null, this.props.definitions.map((def, index) => {
            const name = def.name;
            let input;
            if (def.multiple) {
              let possibleValues = null;
              if (def.enumeration) possibleValues = def.enumeration;else if (def.type === "bool") possibleValues = [false, true];
              const controller = new ComponentPropController(this, name, def.type, possibleValues);
              input = /*#__PURE__*/React.createElement(SetInput, {
                controller: controller,
                values: possibleValues
              });
            } else if (def.enumeration) {
              input = /*#__PURE__*/React.createElement("select", {
                value: this.state[name][0],
                onChange: event => this.onChange(event, def)
              }, def.enumeration.map((value, valueIndex) => /*#__PURE__*/React.createElement("option", {
                key: valueIndex,
                value: value
              }, value)));
            } else if (def.type === "bool") {
              input = /*#__PURE__*/React.createElement("select", {
                value: this.state[name][0],
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
                value: this.state[name][0]
              });
            }
            return /*#__PURE__*/React.createElement("tr", {
              key: index
            }, /*#__PURE__*/React.createElement("td", {
              className: "label"
            }, /*#__PURE__*/React.createElement("strong", null, name)), /*#__PURE__*/React.createElement("td", {
              className: "input"
            }, input));
          }))))));
        }
        onClose() {
          this.props.onClose(this.state);
        }
        onChange(event, def) {
          try {
            this.setState({
              [def.name]: [UTILITIES.parsePropValString(def.type, def.enumeration, event.target.value)]
            });
          } catch (exception) {
            window.alert(exception.toString());
          }
        }
      });
    }
  };
});