System.register(["../dialogs/Dialog.js", "../components/Cell.js", "../language.js"], function (_export, _context) {
  "use strict";

  var Dialog, Cell, LangContext, FormVideosKeywordsToProperty;

  _export("FormVideosKeywordsToProperty", void 0);

  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
    }],
    execute: function () {
      _export("FormVideosKeywordsToProperty", FormVideosKeywordsToProperty = class FormVideosKeywordsToProperty extends React.Component {
        constructor(props) {
          // prop_types: PropertyDefinition[]
          // onClose(name)
          super(props);
          this.state = {
            field: this.props.prop_types[0].name,
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
          }, this.props.prop_types.map((def, i) => /*#__PURE__*/React.createElement("option", {
            key: i,
            value: def.name
          }, tr("Property"), ": ", def.name)))), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            id: "only-empty",
            type: "checkbox",
            checked: this.state.onlyEmpty,
            onChange: this.onChangeEmpty
          }), " ", /*#__PURE__*/React.createElement("label", {
            htmlFor: "only-empty"
          }, tr('only videos without values for property "{name}"', {
            name: this.state.field
          })))));
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

      FormVideosKeywordsToProperty.contextType = LangContext;
    }
  };
});