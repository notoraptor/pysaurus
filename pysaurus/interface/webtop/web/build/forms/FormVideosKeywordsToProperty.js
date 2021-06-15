System.register(["../dialogs/Dialog.js", "../components/Cell.js"], function (_export, _context) {
  "use strict";

  var Dialog, Cell, FormVideosKeywordsToProperty;

  _export("FormVideosKeywordsToProperty", void 0);

  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }],
    execute: function () {
      _export("FormVideosKeywordsToProperty", FormVideosKeywordsToProperty = class FormVideosKeywordsToProperty extends React.Component {
        constructor(props) {
          // properties: PropertyDefinition[]
          // onClose(name)
          super(props);
          this.state = {
            field: this.props.properties[0].name,
            onlyEmpty: false
          };
          this.onChangeGroupField = this.onChangeGroupField.bind(this);
          this.onChangeEmpty = this.onChangeEmpty.bind(this);
          this.onClose = this.onClose.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            title: "Fill property",
            yes: "fill",
            action: this.onClose
          }, /*#__PURE__*/React.createElement(Cell, {
            center: true,
            full: true,
            className: "text-center"
          }, /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("select", {
            value: this.state.field,
            onChange: this.onChangeGroupField
          }, this.props.properties.map((def, i) => /*#__PURE__*/React.createElement("option", {
            key: i,
            value: def.name
          }, "Property: ", def.name)))), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            id: "only-empty",
            type: "checkbox",
            checked: this.state.onlyEmpty,
            onChange: this.onChangeEmpty
          }), ' ', /*#__PURE__*/React.createElement("label", {
            htmlFor: "only-empty"
          }, "only videos without values for property \"", this.state.field, "\""))));
        }

        onChangeGroupField(event) {
          this.setState({
            field: event.target.value
          });
        }

        onChangeEmpty(event) {
          this.setState({
            onlyEmpty: event.target.checked
          });
        }

        onClose() {
          this.props.onClose(this.state);
        }

      });
    }
  };
});