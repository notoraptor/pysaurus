System.register(["../components/SetInput.js", "../dialogs/Dialog.js", "../components/Cell.js", "../utils/backend.js", "../utils/functions.js", "../forms/GenericFormRename.js", "../language.js"], function (_export, _context) {
  "use strict";

  var ComponentPropController, SetInput, Dialog, Cell, backend_error, python_call, utilities, GenericFormRename, LangContext, PropertiesPage, DEFAULT_VALUES;

  function getDefaultValue(propType, isEnum) {
    return isEnum ? [] : DEFAULT_VALUES[propType].toString();
  }

  _export("PropertiesPage", void 0);

  return {
    setters: [function (_componentsSetInputJs) {
      ComponentPropController = _componentsSetInputJs.ComponentPropController;
      SetInput = _componentsSetInputJs.SetInput;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_utilsFunctionsJs) {
      utilities = _utilsFunctionsJs.utilities;
    }, function (_formsGenericFormRenameJs) {
      GenericFormRename = _formsGenericFormRenameJs.GenericFormRename;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
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
          const defaultType = 'str';
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
            className: "block bold h-100 px-4",
            onClick: this.back
          }, "\u2B9C")), /*#__PURE__*/React.createElement("div", {
            className: "text-center flex-grow-1"
          }, this.context.gui_properties_title)), /*#__PURE__*/React.createElement("hr", null), /*#__PURE__*/React.createElement("div", {
            className: "content horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "list text-center"
          }, /*#__PURE__*/React.createElement("h3", {
            className: "text-center"
          }, this.context.gui_properties_current), this.renderPropTypes()), /*#__PURE__*/React.createElement("div", {
            className: "new"
          }, /*#__PURE__*/React.createElement("h3", {
            className: "text-center"
          }, this.context.gui_properties_add_new), /*#__PURE__*/React.createElement("table", {
            className: "first-td-text-right w-100"
          }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
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
          }, this.context.text_boolean), /*#__PURE__*/React.createElement("option", {
            value: "int"
          }, this.context.text_integer), /*#__PURE__*/React.createElement("option", {
            value: "float"
          }, this.context.text_float), /*#__PURE__*/React.createElement("option", {
            value: "str"
          }, this.context.text_text)))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "prop-multiple",
            checked: this.state.multiple,
            onChange: this.onChangeMultiple
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-multiple"
          }, this.context.text_accept_many_values))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "prop-enumeration",
            checked: this.state.enumeration,
            onChange: this.onChangeEnumeration
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-enumeration"
          }, this.context.text_is_enumeration))), !this.state.multiple || this.state.enumeration ? /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: 'prop-default-' + this.state.type
          }, this.state.enumeration ? this.state.multiple ? this.context.gui_properties_enumeration_values_multiple : this.context.gui_properties_enumeration_values : this.context.gui_properties_default_value)), /*#__PURE__*/React.createElement("td", null, this.renderDefaultInput())) : "", /*#__PURE__*/React.createElement("tr", {
            className: "buttons"
          }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "reset block",
            onClick: this.reset
          }, "reset")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "submit bold block",
            onClick: this.submit
          }, "add")))))));
        }

        renderPropTypes() {
          return /*#__PURE__*/React.createElement("table", {
            className: "w-100"
          }, /*#__PURE__*/React.createElement("thead", {
            className: "bold"
          }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "Name"), /*#__PURE__*/React.createElement("th", null, "Type"), /*#__PURE__*/React.createElement("th", null, "Default"), /*#__PURE__*/React.createElement("th", null, "Options"))), /*#__PURE__*/React.createElement("tbody", null, this.state.definitions.map((def, index) => /*#__PURE__*/React.createElement("tr", {
            key: index
          }, /*#__PURE__*/React.createElement("td", {
            className: "name bold"
          }, def.name), /*#__PURE__*/React.createElement("td", {
            className: "type"
          }, def.multiple ? /*#__PURE__*/React.createElement("span", null, this.context.text_one_or_many, "\xA0") : "", /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("code", null, def.type), " ", def.multiple ? this.context.word_values : this.context.word_value), def.enumeration ? /*#__PURE__*/React.createElement("span", null, "\xA0", this.context.word_in, " ", '{', def.enumeration.join(', '), '}') : ""), /*#__PURE__*/React.createElement("td", {
            className: "default"
          }, function () {
            if (def.multiple) {
              return `{${def.defaultValue.join(', ')}}`;
            } else if (def.type === "str") {
              return `"${def.defaultValue}"`;
            } else {
              return def.defaultValue.toString();
            }
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
            const controller = new ComponentPropController(this, 'defaultPropVal', this.state.type, null);
            return /*#__PURE__*/React.createElement(SetInput, {
              className: "block",
              identifier: 'prop-default-' + this.state.type,
              controller: controller
            });
          }

          if (this.state.type === 'bool') {
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
            id: 'prop-default-' + this.state.type,
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
            if (!this.state.enumeration) definition = utilities(this.context).parsePropValString(this.state.type, null, definition);
            python_call('add_prop_type', this.state.name, this.state.type, definition, this.state.multiple).then(definitions => {
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
            title: this.context.form_title_delete_property.format({
              name
            }),
            yes: this.context.text_delete,
            action: () => {
              python_call('delete_prop_type', name).catch(backend_error).then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
              });
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            className: "text-center",
            center: true,
            full: true
          }, /*#__PURE__*/React.createElement("h3", null, this.context.form_content_delete_property.format({
            name
          })))));
        }

        convertPropertyToUnique(name) {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: this.context.form_title_convert_to_unique_property.format({
              name
            }),
            yes: this.context.form_convert_to_unique_property_yes,
            action: () => {
              python_call('convert_prop_to_unique', name).then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
              }).catch(backend_error);
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            className: "text-center",
            center: true,
            full: true
          }, /*#__PURE__*/React.createElement("h3", null, this.context.form_confirm_convert_to_unique_property.format({
            name
          })))));
        }

        convertPropertyToMultiple(name) {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: this.context.form_title_convert_to_multiple_property.format({
              name
            }),
            yes: this.context.form_convert_to_multiple_property_yes,
            action: () => {
              python_call('convert_prop_to_multiple', name).then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
              }).catch(backend_error);
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            className: "text-center",
            center: true,
            full: true
          }, /*#__PURE__*/React.createElement("h3", null, this.context.form_confirm_convert_to_multiple_property.format({
            name
          })))));
        }

        renameProperty(name) {
          Fancybox.load( /*#__PURE__*/React.createElement(GenericFormRename, {
            title: this.context.form_title_rename_property.format({
              name
            }),
            header: this.context.text_rename_property,
            description: name,
            data: name,
            onClose: newName => {
              python_call('rename_property', name, newName).then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
              }).catch(backend_error);
            }
          }));
        }

        getDefaultInputState() {
          const defaultType = 'str';
          return {
            name: "",
            type: defaultType,
            enumeration: false,
            defaultPropVal: getDefaultValue(defaultType),
            multiple: false
          };
        }

      });

      PropertiesPage.contextType = LangContext;
    }
  };
});