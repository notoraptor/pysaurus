System.register(["../dialogs/Dialog.js"], function (_export, _context) {
  "use strict";

  var Dialog, FormEditPropertyValue;

  _export("FormEditPropertyValue", void 0);

  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }],
    execute: function () {
      _export("FormEditPropertyValue", FormEditPropertyValue = class FormEditPropertyValue extends React.Component {
        constructor(props) {
          // properties: {name => def}
          // name: str
          // values: []
          // onClose(operation)
          super(props);
          this.state = {
            form: 'edit',
            value: this.props.values[0].toString(),
            move: '',
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
          const canMove = this.state.otherDefinitions.length && this.props.values.length === 1;
          return /*#__PURE__*/React.createElement(Dialog, {
            yes: this.state.form,
            no: "cancel",
            onClose: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "edit-property-value"
          }, /*#__PURE__*/React.createElement("div", {
            className: "bar text-center"
          }, /*#__PURE__*/React.createElement("button", {
            className: `delete ${this.state.form === 'delete' ? 'selected' : ''}`,
            onClick: this.setDelete
          }, "delete"), /*#__PURE__*/React.createElement("button", {
            className: `edit ${this.state.form === 'edit' ? 'selected' : ''}`,
            onClick: this.setEdit
          }, "edit"), canMove ? /*#__PURE__*/React.createElement("button", {
            className: `move ${this.state.form === 'move' ? 'selected' : ''}`,
            onClick: this.setMove
          }, "move") : ''), /*#__PURE__*/React.createElement("div", {
            className: `form ${this.state.form}`
          }, this.renderForm())));
        }

        renderForm() {
          switch (this.state.form) {
            case 'delete':
              return this.renderDelete();

            case 'edit':
              return this.renderEdit();

            case 'move':
              if (this.props.values.length === 1) return this.renderMove();
              break;

            default:
              break;
          }
        }

        renderDelete() {
          return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", null, "Are you sure you want to delete property value"), /*#__PURE__*/React.createElement("h3", null, "\"", this.props.name, "\" / ", this.valuesToString(), " ?"));
        }

        renderEdit() {
          const name = this.props.name;
          const propVal = this.state.value;
          const def = this.props.properties[name];
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

          return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", null, "Edit property \"", this.props.name, "\" / ", this.valuesToString()), /*#__PURE__*/React.createElement("div", null, input));
        }

        renderMove() {
          const def = this.props.properties[this.props.name];
          return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", null, "Move property \"", this.props.name, "\" / ", this.valuesToString(), " to another property of type \"", def.type, "\"."), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("select", {
            value: this.state.move,
            onChange: this.onMove
          }, this.state.otherDefinitions.map((other, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: other.name
          }, other.name)))));
        }

        getCompatibleDefinitions() {
          const def = this.props.properties[this.props.name];
          const otherDefinitions = [];

          for (let other of Object.values(this.props.properties)) {
            if (def.name !== other.name && def.type === other.type) otherDefinitions.push(other);
          }

          return otherDefinitions;
        }

        setDelete() {
          this.setState({
            form: 'delete'
          });
        }

        setEdit() {
          this.setState({
            form: 'edit',
            value: this.props.value
          });
        }

        setMove() {
          this.setState({
            form: 'move',
            move: this.state.otherDefinitions[0].name
          });
        }

        onEdit(event) {
          const def = this.props.properties[this.props.name];

          try {
            this.setState({
              value: parsePropValString(def.type, def.enumeration, event.target.value)
            });
          } catch (exception) {
            window.alert(exception.toString());
          }
        }

        onEditKeyDown(event) {
          if (event.key === "Enter") {
            this.onClose(true);
          }
        }

        onMove(event) {
          this.setState({
            move: event.target.value
          });
        }

        onClose(yes) {
          this.props.onClose(yes ? Object.assign({}, this.state) : null);
        }

        valuesToString() {
          if (this.props.values.length === 1) return this.props.values[0].toString();
          return `${this.props.values.length} values (${this.props.values[0].toString()} ... ${this.props.values[this.props.values.length - 1].toString()})`;
        }

      });
    }
  };
});