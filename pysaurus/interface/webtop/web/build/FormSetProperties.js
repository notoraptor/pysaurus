System.register(["./SetInput.js", "./Dialog.js"], function (_export, _context) {
  "use strict";

  var ComponentController, SetInput, Dialog, FormSetProperties;

  function generatePropValChecker(propType, values) {
    switch (propType) {
      case "bool":
        return function (value) {
          if (["false", "true"].indexOf(value) < 0) {
            window.alert(`Invalid bool value, expected: [false, true], got ${value}`);
            return false;
          }

          return true;
        };

      case "int":
        return function (value) {
          if (isNaN(parseInt(value))) {
            window.alert(`Unable to parse integer: ${value}`);
            return false;
          }

          return true;
        };

      case "float":
        return function (value) {
          if (isNaN(parseFloat(value))) {
            window.alert(`Unable to parse floating value: ${value}`);
            return false;
          }

          return true;
        };

      case "str":
        return function (value) {
          return true;
        };

      case "enum":
        return function (value) {
          if (values.indexOf(value) < 0) {
            window.alert(`Invalid enum value, expected: [${values.join(', ')}], got ${value}`);
            return false;
          }

          return true;
        };
    }
  }

  _export("FormSetProperties", void 0);

  return {
    setters: [function (_SetInputJs) {
      ComponentController = _SetInputJs.ComponentController;
      SetInput = _SetInputJs.SetInput;
    }, function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }],
    execute: function () {
      _export("FormSetProperties", FormSetProperties = class FormSetProperties extends React.Component {
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
          this.parsePropVal = this.parsePropVal.bind(this);
        }

        render() {
          const data = this.props.data;
          const hasThumbnail = data.hasThumbnail;
          return /*#__PURE__*/React.createElement(Dialog, {
            yes: "save",
            no: "cancel",
            onClose: this.onClose
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
            className: "filename"
          }, /*#__PURE__*/React.createElement("code", null, data.filename)), data.title === data.file_title ? '' : /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, /*#__PURE__*/React.createElement("em", null, data.title))), /*#__PURE__*/React.createElement("div", {
            className: "properties"
          }, /*#__PURE__*/React.createElement("div", {
            className: "table"
          }, this.props.definitions.map((def, index) => {
            const name = def.name;
            let input = null;

            if (def.multiple) {
              let possibleValues = null;

              switch (def.type) {
                case "bool":
                  possibleValues = [false, true];
                  break;

                case "enum":
                  possibleValues = def.values;
                  break;

                default:
                  break;
              }

              const controller = new ComponentController(this, name, value => this.parsePropVal(def, value));
              input = /*#__PURE__*/React.createElement(SetInput, {
                controller: controller,
                values: possibleValues,
                onCheck: generatePropValChecker(def.type, possibleValues)
              });
            } else {
              switch (def.type) {
                case "bool":
                  input = /*#__PURE__*/React.createElement("select", {
                    value: this.state[name],
                    onChange: event => this.onChange(event, def)
                  }, /*#__PURE__*/React.createElement("option", {
                    value: "false"
                  }, "false"), /*#__PURE__*/React.createElement("option", {
                    value: "true"
                  }, "true"));
                  break;

                case "int":
                  input = /*#__PURE__*/React.createElement("input", {
                    type: "number",
                    onChange: event => this.onChange(event, def),
                    value: this.state[name]
                  });
                  break;

                case "enum":
                  input = /*#__PURE__*/React.createElement("select", {
                    value: this.state[name],
                    onChange: event => this.onChange(event, def)
                  }, def.values.map((value, valueIndex) => /*#__PURE__*/React.createElement("option", {
                    key: valueIndex,
                    value: value
                  }, value)));
                  break;

                default:
                  input = /*#__PURE__*/React.createElement("input", {
                    type: "text",
                    onChange: event => this.onChange(event, def),
                    value: this.state[name]
                  });
                  break;
              }
            }

            return /*#__PURE__*/React.createElement("div", {
              className: "table-row",
              key: index
            }, /*#__PURE__*/React.createElement("div", {
              className: "table-cell label"
            }, /*#__PURE__*/React.createElement("strong", null, name)), /*#__PURE__*/React.createElement("div", {
              className: "table-cell input"
            }, input));
          })))));
        }

        onClose(yes) {
          this.props.onClose(yes ? this.state : null);
        }

        onChange(event, def) {
          const value = this.parsePropVal(def, event.target.value);
          if (value !== undefined) this.setState({
            [def.name]: value
          });
        }

        parsePropVal(def, value) {
          const checker = generatePropValChecker(def.type, def.values);

          if (checker(value)) {
            switch (def.type) {
              case "bool":
                return {
                  "false": false,
                  "true": true
                }[value];

              case "int":
                return parseInt(value);

              case "float":
                return parseFloat(value);

              default:
                return value;
            }
          }
        }

      });
    }
  };
});