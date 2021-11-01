System.register(["../utils/constants.js", "../dialogs/Dialog.js", "../language.js"], function (_export, _context) {
  "use strict";

  var getFieldMap, Dialog, LangContext, FormVideosGrouping;

  _export("FormVideosGrouping", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      getFieldMap = _utilsConstantsJs.getFieldMap;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
    }],
    execute: function () {
      _export("FormVideosGrouping", FormVideosGrouping = class FormVideosGrouping extends React.Component {
        constructor(props) {
          // groupDef: GroupDef
          // properties: [PropDef]
          // propertyMap: {name: PropDef}
          // onClose(groupDef)
          super(props);
          this.state = this.props.groupDef.field ? {
            isProperty: this.props.groupDef.is_property,
            field: this.props.groupDef.field,
            sorting: this.props.groupDef.sorting,
            reverse: this.props.groupDef.reverse,
            allowSingletons: this.props.groupDef.allow_singletons
          } : {
            isProperty: false,
            field: undefined,
            sorting: "field",
            reverse: false,
            allowSingletons: undefined
          };
          this.onChangeAllowSingletons = this.onChangeAllowSingletons.bind(this);
          this.onChangeGroupField = this.onChangeGroupField.bind(this);
          this.onChangeSorting = this.onChangeSorting.bind(this);
          this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
          this.onClose = this.onClose.bind(this);
          this.onChangeFieldType = this.onChangeFieldType.bind(this);
          this.getFields = this.getFields.bind(this);
          this.getStateField = this.getStateField.bind(this);
          this.getStateAllowSingletons = this.getStateAllowSingletons.bind(this);
        }

        render() {
          const field = this.getStateField();
          return /*#__PURE__*/React.createElement(Dialog, {
            title: "Group videos:",
            yes: "group",
            action: this.onClose
          }, /*#__PURE__*/React.createElement("table", {
            className: "from-videos-grouping first-td-text-right w-100"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, this.context.text_field_type), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
            id: "field-type-property",
            type: "radio",
            value: "true",
            checked: this.state.isProperty,
            onChange: this.onChangeFieldType
          }), " ", /*#__PURE__*/React.createElement("label", {
            htmlFor: "field-type-property"
          }, "property"), " ", /*#__PURE__*/React.createElement("input", {
            id: "field-type-attribute",
            type: "radio",
            value: "false",
            checked: !this.state.isProperty,
            onChange: this.onChangeFieldType
          }), " ", /*#__PURE__*/React.createElement("label", {
            htmlFor: "field-type-attribute"
          }, "attribute"))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-field"
          }, "Field")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("select", {
            className: "block",
            id: "group-field",
            value: field,
            onChange: this.onChangeGroupField
          }, this.state.isProperty ? this.props.properties.map((def, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: def.name
          }, def.name)) : this.getFields().allowed.map((fieldOption, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: fieldOption.name
          }, fieldOption.title))))), this.state.isProperty || !this.getFields().fields[field].isOnlyMany() ? /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "allow-singletons",
            checked: this.getStateAllowSingletons(),
            onChange: this.onChangeAllowSingletons
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "allow-singletons"
          }, this.context.text_allow_singletons))) : /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, "\xA0"), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("em", null, this.context.text_singletons_auto_disabled))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-sorting"
          }, this.context.text_sort_using)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("select", {
            className: "block",
            id: "group-sorting",
            value: this.state.sorting,
            onChange: this.onChangeSorting
          }, /*#__PURE__*/React.createElement("option", {
            value: "field"
          }, this.context.text_field_value), this.fieldIsString() ? /*#__PURE__*/React.createElement("option", {
            value: "length"
          }, this.context.text_field_value_length) : "", /*#__PURE__*/React.createElement("option", {
            value: "count"
          }, this.context.text_group_size)))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "group-reverse",
            checked: this.state.reverse,
            onChange: this.onChangeGroupReverse
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-reverse"
          }, this.context.text_sort_reverse))))));
        }

        getStateField() {
          return this.state.field === undefined ? this.getFields().allowed[0].name : this.state.field;
        }

        getStateAllowSingletons() {
          return this.state.allowSingletons === undefined ? !this.getFields().allowed[0].isOnlyMany() : this.state.allowSingletons;
        }

        getFields() {
          return getFieldMap(this.context);
        }

        fieldIsString() {
          const field = this.getStateField();
          if (this.state.isProperty) return this.props.propertyMap[field].type === "str";
          return this.getFields().fields[field].isString();
        }

        onChangeFieldType(event) {
          const isProperty = event.target.value === "true";
          const field = isProperty ? this.props.properties[0].name : this.getFields().allowed[0].name;
          const sorting = "field";
          const reverse = false;
          const allowSingletons = isProperty || !this.getFields().allowed[0].isOnlyMany();
          this.setState({
            isProperty,
            field,
            sorting,
            reverse,
            allowSingletons
          });
        }

        onChangeGroupField(event) {
          const field = event.target.value;
          const sorting = "field";
          const reverse = false;
          const allowSingletons = this.state.isProperty || !this.getFields().fields[field].isOnlyMany();
          this.setState({
            field,
            sorting,
            reverse,
            allowSingletons
          });
        }

        onChangeAllowSingletons(event) {
          this.setState({
            allowSingletons: event.target.checked
          });
        }

        onChangeSorting(event) {
          this.setState({
            sorting: event.target.value,
            reverse: false
          });
        }

        onChangeGroupReverse(event) {
          this.setState({
            reverse: event.target.checked
          });
        }

        onClose() {
          this.props.onClose(Object.assign({}, this.state));
        }

      });

      FormVideosGrouping.contextType = LangContext;
    }
  };
});