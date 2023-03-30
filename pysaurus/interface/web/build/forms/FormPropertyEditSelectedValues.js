System.register(["../dialogs/Dialog.js", "../language.js", "../utils/functions.js", "../utils/FancyboxManager.js"], function (_export, _context) {
  "use strict";

  var Dialog, LangContext, tr, UTILITIES, Fancybox, FormPropertyEditSelectedValues;
  _export("FormPropertyEditSelectedValues", void 0);
  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
      tr = _languageJs.tr;
    }, function (_utilsFunctionsJs) {
      UTILITIES = _utilsFunctionsJs.UTILITIES;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }],
    execute: function () {
      _export("FormPropertyEditSelectedValues", FormPropertyEditSelectedValues = class FormPropertyEditSelectedValues extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            form: "edit",
            value: this.props.values[0].toString(),
            move: "",
            otherDefinitions: this.getCompatibleDefinitions()
          };
          this.setDelete = this.setDelete.bind(this);
          this.setEdit = this.setEdit.bind(this);
          this.setMove = this.setMove.bind(this);
          this.onEdit = this.onEdit.bind(this);
          this.onMove = this.onMove.bind(this);
          this.onClose = this.onClose.bind(this);
          this.onEditKeyDown = this.onEditKeyDown.bind(this);
          this.valuesToString = this.valuesToString.bind(this);
        }
        render() {
          const canMove = this.state.otherDefinitions.length;
          const values = this.props.values;
          let title;
          if (values.length === 1) title = tr('Property "{name}", value "{value}"', {
            name: this.props.name,
            value: values[0]
          });else title = tr('Property "{name}", {count} values"', {
            name: this.props.name,
            count: values.length
          });
          return /*#__PURE__*/React.createElement(Dialog, {
            title: title,
            yes: this.state.form,
            action: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-property-edit-selected-values vertical flex-grow-1"
          }, /*#__PURE__*/React.createElement("div", {
            className: "bar flex-shrink-0 text-center"
          }, /*#__PURE__*/React.createElement("button", {
            className: `delete ${this.state.form === "delete" ? "selected bolder" : ""}`,
            onClick: this.setDelete
          }, "delete"), /*#__PURE__*/React.createElement("button", {
            className: `edit ${this.state.form === "edit" ? "selected bolder" : ""}`,
            onClick: this.setEdit
          }, "edit"), canMove ? /*#__PURE__*/React.createElement("button", {
            className: `move ${this.state.form === "move" ? "selected bolder" : ""}`,
            onClick: this.setMove
          }, "move") : ""), /*#__PURE__*/React.createElement("div", {
            className: `form position-relative flex-grow-1 text-center ${this.state.form}`
          }, this.renderForm())));
        }
        renderForm() {
          switch (this.state.form) {
            case "delete":
              return this.renderDelete();
            case "edit":
              return this.renderEdit();
            case "move":
              return this.renderMove();
            default:
              break;
          }
        }
        renderDelete() {
          return /*#__PURE__*/React.createElement("div", {
            className: "flex-grow-1"
          }, tr(`
### Are you sure you want to delete property value

### "{name}" / {value} ?
`, {
            name: this.props.name,
            value: this.valuesToString()
          }, "markdown"));
        }
        renderEdit() {
          const name = this.props.name;
          const propVal = this.state.value;
          const def = this.props.definitions[name];
          let input;
          if (def.enumeration) {
            input = /*#__PURE__*/React.createElement("select", {
              value: propVal,
              onChange: this.onEdit
            }, def.enumeration.map((value, valueIndex) => /*#__PURE__*/React.createElement("option", {
              key: valueIndex,
              value: value
            }, value)));
          } else if (def.type === "bool") {
            input = /*#__PURE__*/React.createElement("select", {
              value: propVal,
              onChange: this.onEdit
            }, /*#__PURE__*/React.createElement("option", {
              value: "false"
            }, "false"), /*#__PURE__*/React.createElement("option", {
              value: "true"
            }, "true"));
          } else {
            input = /*#__PURE__*/React.createElement("input", {
              type: def.type === "int" ? "number" : "text",
              onChange: this.onEdit,
              value: propVal,
              onKeyDown: this.onEditKeyDown
            });
          }
          return /*#__PURE__*/React.createElement("div", {
            className: "flex-grow-1"
          }, /*#__PURE__*/React.createElement("h3", null, tr('Edit property "{name}" / {value}', {
            name: this.props.name,
            value: this.valuesToString()
          })), /*#__PURE__*/React.createElement("div", null, input));
        }
        renderMove() {
          const def = this.props.definitions[this.props.name];
          return /*#__PURE__*/React.createElement("div", {
            className: "flex-grow-1"
          }, /*#__PURE__*/React.createElement("h3", null, tr('Move property "{name}" / {value} to another property of type "{type}".', {
            name: this.props.name,
            value: this.valuesToString(),
            type: def.type
          })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("select", {
            value: this.state.move,
            onChange: this.onMove
          }, this.state.otherDefinitions.map((other, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: other.name
          }, other.name)))));
        }
        getCompatibleDefinitions() {
          const def = this.props.definitions[this.props.name];
          const otherDefinitions = [];
          for (let other of Object.values(this.props.definitions)) {
            if (def.name !== other.name && def.type === other.type) otherDefinitions.push(other);
          }
          return otherDefinitions;
        }
        setDelete() {
          this.setState({
            form: "delete"
          });
        }
        setEdit() {
          this.setState({
            form: "edit",
            value: this.props.value
          });
        }
        setMove() {
          this.setState({
            form: "move",
            move: this.state.otherDefinitions[0].name
          });
        }
        onEdit(event) {
          const def = this.props.definitions[this.props.name];
          try {
            this.setState({
              value: UTILITIES.parsePropValString(def.type, def.enumeration, event.target.value)
            });
          } catch (exception) {
            window.alert(exception.toString());
          }
        }
        onEditKeyDown(event) {
          if (event.key === "Enter") {
            Fancybox.close();
            this.onClose();
          }
        }
        onMove(event) {
          this.setState({
            move: event.target.value
          });
        }
        onClose() {
          this.props.onClose(Object.assign({}, this.state));
        }
        valuesToString() {
          if (this.props.values.length === 1) return this.props.values[0].toString();
          return tr("{count} values ({first} ... {last})", {
            count: this.props.values.length,
            first: this.props.values[0],
            last: this.props.values[this.props.values.length - 1]
          });
        }
      });
      FormPropertyEditSelectedValues.contextType = LangContext;
      FormPropertyEditSelectedValues.propTypes = {
        definitions: PropTypes.object.isRequired,
        name: PropTypes.string.isRequired,
        values: PropTypes.array.isRequired,
        // onClose(object)
        onClose: PropTypes.func.isRequired
      };
    }
  };
});