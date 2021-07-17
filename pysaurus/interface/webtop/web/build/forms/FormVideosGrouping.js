System.register(["../utils/constants.js", "../dialogs/Dialog.js"], function (_export, _context) {
  "use strict";

  var FIELD_MAP, Dialog, FormVideosGrouping;

  _export("FormVideosGrouping", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      FIELD_MAP = _utilsConstantsJs.FIELD_MAP;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
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
            field: FIELD_MAP.allowed[0].name,
            sorting: "field",
            reverse: false,
            allowSingletons: !FIELD_MAP.allowed[0].isOnlyMany()
          };
          this.onChangeAllowSingletons = this.onChangeAllowSingletons.bind(this);
          this.onChangeGroupField = this.onChangeGroupField.bind(this);
          this.onChangeSorting = this.onChangeSorting.bind(this);
          this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
          this.onClose = this.onClose.bind(this);
          this.onChangeFieldType = this.onChangeFieldType.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            title: "Group videos:",
            yes: "group",
            action: this.onClose
          }, /*#__PURE__*/React.createElement("table", {
            className: "form-group first-td-text-right"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, "Field type"), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
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
            id: "group-field",
            value: this.state.field,
            onChange: this.onChangeGroupField
          }, this.state.isProperty ? this.props.properties.map((def, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: def.name
          }, def.name)) : FIELD_MAP.allowed.map((fieldOption, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: fieldOption.name
          }, fieldOption.title))))), this.state.isProperty || !FIELD_MAP.fields[this.state.field].isOnlyMany() ? /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "allow-singletons",
            checked: this.state.allowSingletons,
            onChange: this.onChangeAllowSingletons
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "allow-singletons"
          }, "Allow singletons (groups with only 1 video)"))) : /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, "\xA0"), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("em", null, "Will look for groups with at least 2 videos."))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-sorting"
          }, "Sort using:")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("select", {
            id: "group-sorting",
            value: this.state.sorting,
            onChange: this.onChangeSorting
          }, /*#__PURE__*/React.createElement("option", {
            value: "field"
          }, "Field value"), this.fieldIsString() ? /*#__PURE__*/React.createElement("option", {
            value: "length"
          }, "Field value length") : '', /*#__PURE__*/React.createElement("option", {
            value: "count"
          }, "Group size")))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "group-reverse",
            checked: this.state.reverse,
            onChange: this.onChangeGroupReverse
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-reverse"
          }, "sort in reverse order"))))));
        }

        fieldIsString() {
          if (this.state.isProperty) return this.props.propertyMap[this.state.field].type === "str";
          return FIELD_MAP.fields[this.state.field].isString;
        }

        onChangeFieldType(event) {
          const isProperty = event.target.value === "true";
          const field = isProperty ? this.props.properties[0].name : FIELD_MAP.allowed[0].name;
          const sorting = "field";
          const reverse = false;
          const allowSingletons = isProperty || !FIELD_MAP.allowed[0].isOnlyMany();
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
          const allowSingletons = this.state.isProperty || !FIELD_MAP.fields[field].isOnlyMany();
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
    }
  };
});