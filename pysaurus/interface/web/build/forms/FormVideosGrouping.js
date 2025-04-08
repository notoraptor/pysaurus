System.register(["../dialogs/Dialog.js", "../language.js", "../utils/constants.js", "../BaseComponent.js"], function (_export, _context) {
  "use strict";

  var Dialog, tr, FIELD_MAP, BaseComponent, FormVideosGrouping;
  _export("FormVideosGrouping", void 0);
  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_languageJs) {
      tr = _languageJs.tr;
    }, function (_utilsConstantsJs) {
      FIELD_MAP = _utilsConstantsJs.FIELD_MAP;
    }, function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }],
    execute: function () {
      _export("FormVideosGrouping", FormVideosGrouping = class FormVideosGrouping extends BaseComponent {
        // groupDef: GroupDef
        // prop_types: [PropDef]
        // propertyMap: {name: PropDef}
        // onClose(groupDef)

        getInitialState() {
          return this.props.groupDef.field ? {
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
          }, tr("Field type")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("input", {
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
          }, this.state.isProperty ? this.props.prop_types.map((def, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: def.name
          }, def.name)) : FIELD_MAP.allowed.map((fieldOption, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: fieldOption.name
          }, fieldOption.title))))), this.state.isProperty || !FIELD_MAP.fields[field].isOnlyMany() ? /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "allow-singletons",
            checked: this.getStateAllowSingletons(),
            onChange: this.onChangeAllowSingletons
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "allow-singletons"
          }, tr("Allow singletons (groups with only 1 video)")))) : /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, "\xA0"), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("em", null, tr("Will look for groups with at least 2 videos.")))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-sorting"
          }, tr("Sort using:"))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("select", {
            className: "block",
            id: "group-sorting",
            value: this.state.sorting,
            onChange: this.onChangeSorting
          }, /*#__PURE__*/React.createElement("option", {
            value: "field"
          }, tr("Field value")), this.fieldIsString() ? /*#__PURE__*/React.createElement("option", {
            value: "length"
          }, tr("Field value length")) : "", /*#__PURE__*/React.createElement("option", {
            value: "count"
          }, tr("Group size"))))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "group-reverse",
            checked: this.state.reverse,
            onChange: this.onChangeGroupReverse
          })), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-reverse"
          }, tr("sort in reverse order")))))));
        }
        getStateField() {
          return this.state.field === undefined ? FIELD_MAP.allowed[0].name : this.state.field;
        }
        getStateAllowSingletons() {
          return this.state.allowSingletons === undefined ? !FIELD_MAP.allowed[0].isOnlyMany() : this.state.allowSingletons;
        }
        fieldIsString() {
          const field = this.getStateField();
          if (this.state.isProperty) return this.props.propertyMap[field].type === "str";
          return FIELD_MAP.fields[field].isString();
        }
        onChangeFieldType(event) {
          const isProperty = event.target.value === "true";
          const field = isProperty ? this.props.prop_types[0].name : FIELD_MAP.allowed[0].name;
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
          this.props.onClose(Object.assign({}, {
            isProperty: this.state.isProperty,
            field: this.getStateField(),
            sorting: this.state.sorting,
            reverse: this.state.reverse,
            allowSingletons: this.getStateAllowSingletons()
          }));
        }
      });
    }
  };
});