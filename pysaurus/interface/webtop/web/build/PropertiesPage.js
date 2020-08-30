System.register(["./SetInput.js", "./Dialog.js", "./Cell.js"], function (_export, _context) {
  "use strict";

  var SetInput, ComponentController, Dialog, Cell, PropertiesPage, DEFAULT_VALUES;

  function getDefaultValue(propType) {
    return DEFAULT_VALUES[propType].toString();
  }

  _export("PropertiesPage", void 0);

  return {
    setters: [function (_SetInputJs) {
      SetInput = _SetInputJs.SetInput;
      ComponentController = _SetInputJs.ComponentController;
    }, function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }, function (_CellJs) {
      Cell = _CellJs.Cell;
    }],
    execute: function () {
      DEFAULT_VALUES = {
        bool: false,
        int: 0,
        float: 0.0,
        str: ''
      };

      _export("PropertiesPage", PropertiesPage = class PropertiesPage extends React.Component {
        constructor(props) {
          // app: App
          // parameters {definitons}
          super(props);
          const definitions = this.props.parameters.definitions;
          const defaultType = 'str';
          this.state = {
            definitions: definitions,
            name: '',
            type: defaultType,
            enumeration: true,
            defaultValue: getDefaultValue(defaultType),
            multiple: false
          };
          this.setType = this.setType.bind(this);
          this.back = this.back.bind(this);
          this.onChangeName = this.onChangeName.bind(this);
          this.onChangeType = this.onChangeType.bind(this);
          this.onChangeDefault = this.onChangeDefault.bind(this);
          this.onChangeMultiple = this.onChangeMultiple.bind(this);
          this.onChangeEnumeration = this.onChangeEnumeration.bind(this);
          this.reset = this.reset.bind(this);
          this.submit = this.submit.bind(this);
          this.deleteProperty = this.deleteProperty.bind(this);
          this.getDefaultInputState = this.getDefaultInputState.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            id: "properties"
          }, /*#__PURE__*/React.createElement("h2", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "back"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.back
          }, "\u2B9C")), /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, "Properties Management")), /*#__PURE__*/React.createElement("hr", null), /*#__PURE__*/React.createElement("div", {
            className: "content horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "list"
          }, /*#__PURE__*/React.createElement("h3", null, "Current properties"), this.renderPropTypes()), /*#__PURE__*/React.createElement("div", {
            className: "new"
          }, /*#__PURE__*/React.createElement("h3", null, "Add a new property"), /*#__PURE__*/React.createElement("div", {
            className: "entries"
          }, /*#__PURE__*/React.createElement("div", {
            className: "entry"
          }, /*#__PURE__*/React.createElement("div", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-name"
          }, "Name:")), /*#__PURE__*/React.createElement("div", {
            className: "input"
          }, /*#__PURE__*/React.createElement("input", {
            type: "text",
            name: "name",
            id: "prop-name",
            value: this.state.name,
            onChange: this.onChangeName
          }))), /*#__PURE__*/React.createElement("div", {
            className: "entry"
          }, /*#__PURE__*/React.createElement("div", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-type"
          }, "Type:")), /*#__PURE__*/React.createElement("div", {
            className: "input"
          }, /*#__PURE__*/React.createElement("select", {
            name: "type",
            id: "prop-type",
            value: this.state.type,
            onChange: this.onChangeType
          }, /*#__PURE__*/React.createElement("option", {
            value: "bool"
          }, "boolean"), /*#__PURE__*/React.createElement("option", {
            value: "int"
          }, "integer"), /*#__PURE__*/React.createElement("option", {
            value: "float"
          }, "floating number"), /*#__PURE__*/React.createElement("option", {
            value: "str"
          }, "text")))), /*#__PURE__*/React.createElement("div", {
            className: "entry"
          }, /*#__PURE__*/React.createElement("div", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            name: "multiple",
            id: "prop-multiple",
            checked: this.state.multiple,
            onChange: this.onChangeMultiple
          })), /*#__PURE__*/React.createElement("div", {
            className: "input"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-multiple"
          }, "accept many values"))), /*#__PURE__*/React.createElement("div", {
            className: "entry"
          }, /*#__PURE__*/React.createElement("div", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            name: "enumeration",
            id: "prop-enumeration",
            checked: this.state.enumeration,
            onChange: this.onChangeEnumeration
          })), /*#__PURE__*/React.createElement("div", {
            className: "input"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "prop-enumeration"
          }, "Is enumeration"))), this.state.multiple && !this.state.enumeration ? '' : /*#__PURE__*/React.createElement("div", {
            className: "entry"
          }, /*#__PURE__*/React.createElement("div", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: 'prop-default-' + this.state.type
          }, this.state.enumeration ? 'Enumeration values' + (this.state.multiple ? '' : ' (first is default)') : 'Default value')), /*#__PURE__*/React.createElement("div", {
            className: "input"
          }, this.renderDefaultInput())), /*#__PURE__*/React.createElement("div", {
            className: "entry buttons"
          }, /*#__PURE__*/React.createElement("div", {
            className: "label"
          }, /*#__PURE__*/React.createElement("button", {
            className: "reset",
            onClick: this.reset
          }, "reset")), /*#__PURE__*/React.createElement("div", {
            className: "input"
          }, /*#__PURE__*/React.createElement("button", {
            className: "submit",
            onClick: this.submit
          }, "add")))))));
        }

        renderPropTypes() {
          return /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "Name"), /*#__PURE__*/React.createElement("th", null, "Type"), /*#__PURE__*/React.createElement("th", null, "Default"), /*#__PURE__*/React.createElement("th", null, "Options"))), /*#__PURE__*/React.createElement("tbody", null, this.state.definitions.map((def, index) => /*#__PURE__*/React.createElement("tr", {
            key: index
          }, /*#__PURE__*/React.createElement("td", {
            className: "name"
          }, def.name), /*#__PURE__*/React.createElement("td", {
            className: "type"
          }, def.multiple ? /*#__PURE__*/React.createElement("span", null, "one or many\xA0") : '', /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("code", null, def.type), " value", def.multiple ? 's' : ''), def.enumeration ? /*#__PURE__*/React.createElement("span", null, "\xA0in ", '{', def.enumeration.join(', '), '}') : ''), /*#__PURE__*/React.createElement("td", {
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
          }, /*#__PURE__*/React.createElement("button", {
            className: "delete",
            onClick: () => this.deleteProperty(def.name)
          }, "delete"))))));
        }

        renderDefaultInput() {
          if (this.state.enumeration) {
            const controller = new ComponentController(this, 'defaultValue', value => parsePropValString(this.state.type, null, value));
            return /*#__PURE__*/React.createElement(SetInput, {
              identifier: 'prop-default-' + this.state.type,
              controller: controller
            });
          }

          if (this.state.type === 'bool') {
            return /*#__PURE__*/React.createElement("select", {
              className: "prop-default",
              id: "prop-default-bool",
              value: this.state.defaultValue,
              onChange: this.onChangeDefault
            }, /*#__PURE__*/React.createElement("option", {
              value: "false"
            }, "false"), /*#__PURE__*/React.createElement("option", {
              value: "true"
            }, "true"));
          }

          return /*#__PURE__*/React.createElement("input", {
            type: this.state.type === "int" ? "number" : "text",
            className: "prop-default",
            id: 'prop-default-' + this.state.type,
            onChange: this.onChangeDefault,
            value: this.state.defaultValue
          });
        }

        setType(value) {
          if (this.state.type !== value) this.setState({
            type: value,
            enumeration: false,
            defaultValue: getDefaultValue(value),
            multiple: false
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
          this.setType(event.target.value);
        }

        onChangeDefault(event) {
          const defaultValue = event.target.value;
          if (this.state.defaultValue !== defaultValue) this.setState({
            defaultValue
          });
        }

        onChangeMultiple(event) {
          this.setState({
            multiple: event.target.checked
          });
        }

        onChangeEnumeration(event) {
          const enumeration = event.target.checked;
          const defaultValue = enumeration ? [] : getDefaultValue(this.state.type);
          this.setState({
            enumeration,
            defaultValue
          });
        }

        reset() {
          this.setState(this.getDefaultInputState());
        }

        submit() {
          try {
            let definition = this.state.defaultValue;
            if (!this.state.enumeration) definition = parsePropValString(this.state.type, null, definition);
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
          this.props.app.loadDialog(`Delete property "${name}"?`, onClose => /*#__PURE__*/React.createElement(Dialog, {
            yes: 'delete',
            no: 'cancel',
            onClose: yes => {
              onClose();

              if (yes) {
                python_call('delete_prop_type', name).catch(backend_error).then(definitions => {
                  const state = this.getDefaultInputState();
                  state.definitions = definitions;
                  this.setState(state);
                });
              }
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            className: "text-center",
            center: true,
            full: true
          }, /*#__PURE__*/React.createElement("h3", null, "Are you sure you want to delete property \"", name, "\"?"))));
        }

        getDefaultInputState() {
          const defaultType = 'str';
          return {
            name: '',
            type: defaultType,
            enumeration: false,
            defaultValue: getDefaultValue(defaultType),
            multiple: false
          };
        }

      });
    }
  };
});