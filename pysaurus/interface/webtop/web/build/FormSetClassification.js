System.register(["./Dialog.js", "./Cell.js"], function (_export, _context) {
  "use strict";

  var Dialog, Cell, FormSetClassification;

  _export("FormSetClassification", void 0);

  return {
    setters: [function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }, function (_CellJs) {
      Cell = _CellJs.Cell;
    }],
    execute: function () {
      _export("FormSetClassification", FormSetClassification = class FormSetClassification extends React.Component {
        constructor(props) {
          // properties: PropertyDefinition[]
          // onClose(name)
          super(props);
          this.state = {
            field: this.props.properties[0].name
          };
          this.onChangeGroupField = this.onChangeGroupField.bind(this);
          this.onClose = this.onClose.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            yes: "classify",
            no: "cancel",
            onClose: this.onClose
          }, /*#__PURE__*/React.createElement(Cell, {
            center: true,
            full: true,
            className: "text-center"
          }, /*#__PURE__*/React.createElement("select", {
            value: this.state.field,
            onChange: this.onChangeGroupField
          }, this.props.properties.map((def, i) => /*#__PURE__*/React.createElement("option", {
            key: i,
            value: def.name
          }, "Property: ", def.name)))));
        }

        onChangeGroupField(event) {
          this.setState({
            field: event.target.value
          });
        }

        onClose(yes) {
          this.props.onClose(yes ? this.state.field : null);
        }

      });
    }
  };
});