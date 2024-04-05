System.register(["../components/Cell.js", "../components/SetInput.js", "../dialogs/Dialog.js", "../forms/GenericFormRename.js", "../language.js", "../utils/FancyboxManager.js", "../utils/backend.js", "../utils/functions.js"], function (_export, _context) {
  "use strict";

  var Cell, ComponentPropController, SetInput, Dialog, GenericFormRename, tr, Fancybox, backend_error, python_multiple_call, UTILITIES, PropertiesPage, DEFAULT_VALUES;
  function getDefaultValue(propType, isEnum) {
    return isEnum ? [] : DEFAULT_VALUES[propType].toString();
  }
  _export("PropertiesPage", void 0);
  return {
    setters: [function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }, function (_componentsSetInputJs) {
      ComponentPropController = _componentsSetInputJs.ComponentPropController;
      SetInput = _componentsSetInputJs.SetInput;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_formsGenericFormRenameJs) {
      GenericFormRename = _formsGenericFormRenameJs.GenericFormRename;
    }, function (_languageJs) {
      tr = _languageJs.tr;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_multiple_call = _utilsBackendJs.python_multiple_call;
    }, function (_utilsFunctionsJs) {
      UTILITIES = _utilsFunctionsJs.UTILITIES;
    }],
    execute: function () {
      DEFAULT_VALUES = {
        bool: false,
        int: 0,
        float: 0.0,
        str: ""
      };
      _export("PropertiesPage", PropertiesPage = class PropertiesPage extends React.Component {
        constructor(props) {
          // app: App
          // parameters {definitions}
          super(props);
          const definitions = this.props.parameters.definitions;
          const defaultType = "str";
          this.state = {
            definitions: definitions,
            name: "",
            type: defaultType,
            enumeration: true,
            defaultPropVal: getDefaultValue(defaultType, true),
            multiple: false
          };
          this.back = this.back.bind(this);
          this.onChangeName = this.onChangeName.bind(this);
          this.onChangeType = this.onChangeType.bind(this);
          this.onChangeDefault = this.onChangeDefault.bind(this);
          this.onChangeMultiple = this.onChangeMultiple.bind(this);
          this.onChangeEnumeration = this.onChangeEnumeration.bind(this);
          this.reset = this.reset.bind(this);
          this.submit = this.submit.bind(this);
          this.deleteProperty = this.deleteProperty.bind(this);
          this.renameProperty = this.renameProperty.bind(this);
          this.getDefaultInputState = this.getDefaultInputState.bind(this);
        }
        render() {
          return /*#__PURE__*/React.createElement("div", {
            id: "properties"
          }, /*#__PURE__*/React.createElement("h2", {
            className: "horizontal ml-1 mr-1"
          }, /*#__PURE__*/React.createElement("div", {
            className: "back position-relative"
          }, /*#__PURE__*/React.createElement("button", {
            className: "block h-100 px-4",
            onClick: this.back
          }, /*#__PURE__*/React.createElement("strong", null, "\u2B9C"))), /*#__PURE__*/React.createElement("div", {
            className: "text-center flex-grow-1"
          }, tr("Properties Management"))), /*#__PURE__*/React.createElement("hr", null), /*#__PURE__*/React.createElement("div", {
            className: "content horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "list text-center"
          }, /*#__PURE__*/React.createElement("h3", {
            className: "text-center"
          }, tr("Current properties")), this.renderPropTypes()), /*#__PURE__*/React.createElement("div", {
            className: "new"
          }, /*#__PURE__*/React.createElement("h3", {
            className: "text-center"
          }, tr("Add a new property")), /*#__PURE__*/React.createElement("table", {
            className: "first-td-text-right w-100"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-name"
          }, "Name:")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
            type: "text",
            id: "prop-name",
            className: "block",
            value: this.state.name,
            onChange: this.onChangeName
          }))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-type"
          }, "Type:")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("select", {
            id: "prop-type",
            className: "block",
            value: this.state.type,
            onChange: this.onChangeType
          }, /*#__PURE__*/React.createElement("option", {
            value: "bool"
          }, tr("boolean")), /*#__PURE__*/React.createElement("option", {
            value: "int"
          }, tr("integer")), /*#__PURE__*/React.createElement("option", {
            value: "float"
          }, tr("floating number")), /*#__PURE__*/React.createElement("option", {
            value: "str"
          }, tr("text"))))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "prop-multiple",
            checked: this.state.multiple,
            onChange: this.onChangeMultiple
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-multiple"
          }, tr("accept many values")))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "prop-enumeration",
            checked: this.state.enumeration,
            onChange: this.onChangeEnumeration
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-enumeration"
          }, tr("Is enumeration")))), !this.state.multiple || this.state.enumeration ? /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-default-" + this.state.type
          }, this.state.enumeration ? this.state.multiple ? tr("Enumeration values (first is default)") : tr("Enumeration values") : tr("Default value"))), /*#__PURE__*/React.createElement("td", null, this.renderDefaultInput())) : "", /*#__PURE__*/React.createElement("tr", {
            className: "buttons"
          }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "reset block",
            onClick: this.reset
          }, "reset")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "submit block",
            onClick: this.submit
          }, /*#__PURE__*/React.createElement("strong", null, "add")))))))));
        }
        renderPropTypes() {
          return /*#__PURE__*/React.createElement("table", {
            className: "w-100"
          }, /*#__PURE__*/React.createElement("thead", {
            className: "bold"
          }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "Name"), /*#__PURE__*/React.createElement("th", null, "Type"), /*#__PURE__*/React.createElement("th", null, "Default"), /*#__PURE__*/React.createElement("th", null, "Options"))), /*#__PURE__*/React.createElement("tbody", null, this.state.definitions.map((def, index) => /*#__PURE__*/React.createElement("tr", {
            key: index
          }, /*#__PURE__*/React.createElement("td", {
            className: "name"
          }, /*#__PURE__*/React.createElement("strong", null, def.name)), /*#__PURE__*/React.createElement("td", {
            className: "type"
          }, def.multiple ? /*#__PURE__*/React.createElement("span", null, tr("one or many"), "\xA0") : "", /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("code", null, def.type), " ", def.multiple ? tr("values") : tr("value")), def.enumeration ? /*#__PURE__*/React.createElement("span", null, "\xA0", tr("in"), " ", "{", def.enumeration.join(", "), "}") : ""), /*#__PURE__*/React.createElement("td", {
            className: "default"
          }, function () {
            let values = def.defaultValues;
            if (def.type === "str") values = values.map(el => `"${el}"`);else values = values.map(el => el.toString());
            let output = values.join(", ");
            if (def.multiple) {
              output = `{${output}}`;
            }
            return output;
          }()), /*#__PURE__*/React.createElement("td", {
            className: "options"
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("button", {
            className: "delete red-flag",
            onClick: () => this.deleteProperty(def.name)
          }, "delete")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("button", {
            className: "rename",
            onClick: () => this.renameProperty(def.name)
          }, "rename")), def.multiple ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("button", {
            className: "convert-to-unique",
            onClick: () => this.convertPropertyToUnique(def.name)
          }, "convert to unique")) : /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("button", {
            className: "convert-to-multiple",
            onClick: () => this.convertPropertyToMultiple(def.name)
          }, "convert to multiple")))))));
        }
        renderDefaultInput() {
          if (this.state.enumeration) {
            const controller = new ComponentPropController(this, "defaultPropVal", this.state.type, null);
            return /*#__PURE__*/React.createElement(SetInput, {
              className: "block",
              identifier: "prop-default-" + this.state.type,
              controller: controller
            });
          }
          if (this.state.type === "bool") {
            return /*#__PURE__*/React.createElement("select", {
              className: "prop-default block",
              id: "prop-default-bool",
              value: this.state.defaultPropVal,
              onChange: this.onChangeDefault
            }, /*#__PURE__*/React.createElement("option", {
              value: "false"
            }, "false"), /*#__PURE__*/React.createElement("option", {
              value: "true"
            }, "true"));
          }
          return /*#__PURE__*/React.createElement("input", {
            type: this.state.type === "int" ? "number" : "text",
            className: "prop-default block",
            id: "prop-default-" + this.state.type,
            onChange: this.onChangeDefault,
            value: this.state.defaultPropVal
          });
        }
        back() {
          this.props.app.loadVideosPage();
        }
        onChangeName(event) {
          const name = event.target.value;
          if (this.state.name !== name) this.setState({
            name
          });
        }
        onChangeType(event) {
          const value = event.target.value;
          if (this.state.type !== value) this.setState({
            type: value,
            enumeration: false,
            defaultPropVal: getDefaultValue(value),
            multiple: false
          });
        }
        onChangeDefault(event) {
          const defaultPropVal = event.target.value;
          if (this.state.defaultPropVal !== defaultPropVal) this.setState({
            defaultPropVal
          });
        }
        onChangeMultiple(event) {
          this.setState({
            multiple: event.target.checked
          });
        }
        onChangeEnumeration(event) {
          const enumeration = event.target.checked;
          const defaultPropVal = getDefaultValue(this.state.type, enumeration);
          this.setState({
            enumeration,
            defaultPropVal
          });
        }
        reset() {
          this.setState(this.getDefaultInputState());
        }
        submit() {
          try {
            let definition = this.state.defaultPropVal;
            if (!this.state.enumeration) definition = UTILITIES.parsePropValString(this.state.type, null, definition);
            python_multiple_call(["create_prop_type", this.state.name, this.state.type, definition, this.state.multiple], ["describe_prop_types"]).then(definitions => {
              const state = this.getDefaultInputState();
              state.definitions = definitions;
              this.setState(state);
            }).catch(backend_error);
          } catch (exception) {
            window.alert(exception.toString());
          }
        }
        deleteProperty(name) {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: tr('Delete property "{name}"?', {
              name
            }),
            yes: tr("DELETE"),
            action: () => {
              python_multiple_call(["remove_prop_type", name], ["describe_prop_types"]).catch(backend_error).then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
              });
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            className: "text-center",
            center: true,
            full: true
          }, /*#__PURE__*/React.createElement("h3", null, tr('Are you sure you want to delete property "{name}"?', {
            name
          })))));
        }
        convertPropertyToUnique(name) {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: tr('Convert to unique property "{name}"?', {
              name
            }),
            yes: tr("convert to unique"),
            action: () => {
              python_multiple_call(["convert_prop_multiplicity", name, false], ["describe_prop_types"]).then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
              }).catch(backend_error);
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            className: "text-center",
            center: true,
            full: true
          }, /*#__PURE__*/React.createElement("h3", null, tr('Are you sure you want to convert to unique property "{name}"?', {
            name
          })))));
        }
        convertPropertyToMultiple(name) {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: tr('Convert to multiple property "{name}"?', {
              name
            }),
            yes: tr("convert to multiple"),
            action: () => {
              python_multiple_call(["convert_prop_multiplicity", name, true], ["describe_prop_types"]).then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
              }).catch(backend_error);
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            className: "text-center",
            center: true,
            full: true
          }, /*#__PURE__*/React.createElement("h3", null, tr('Are you sure you want to convert to multiple property "{name}"?', {
            name
          })))));
        }
        renameProperty(name) {
          Fancybox.load( /*#__PURE__*/React.createElement(GenericFormRename, {
            title: tr('Rename property "{name}"?', {
              name
            }),
            header: tr("Rename property"),
            description: name,
            data: name,
            onClose: newName => {
              python_multiple_call(["rename_prop_type", name, newName], ["describe_prop_types"]).then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
              }).catch(backend_error);
            }
          }));
        }
        getDefaultInputState() {
          const defaultType = "str";
          return {
            name: "",
            type: defaultType,
            enumeration: false,
            defaultPropVal: getDefaultValue(defaultType),
            multiple: false
          };
        }
      });
    }
  };
});