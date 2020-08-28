System.register(["./constants.js", "./Dialog.js"], function (_export, _context) {
  "use strict";

  var FIELDS_GROUP_DEF, GroupPermission, SORTED_FIELDS_AND_TITLES, STRING_FIELDS, Dialog, FormGroup, REVERSE_VALUES;

  _export("FormGroup", void 0);

  return {
    setters: [function (_constantsJs) {
      FIELDS_GROUP_DEF = _constantsJs.FIELDS_GROUP_DEF;
      GroupPermission = _constantsJs.GroupPermission;
      SORTED_FIELDS_AND_TITLES = _constantsJs.SORTED_FIELDS_AND_TITLES;
      STRING_FIELDS = _constantsJs.STRING_FIELDS;
    }, function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }],
    execute: function () {
      REVERSE_VALUES = {
        "true": true,
        "false": false
      };

      _export("FormGroup", FormGroup = class FormGroup extends React.Component {
        constructor(props) {
          // definition: GroupDef
          // onClose(groupDef)
          super(props);
          this.state = {
            field: this.props.definition.field || '',
            sorting: this.props.definition.sorting || 'field',
            reverse: this.props.definition.reverse || false,
            allowSingletons: this.props.definition.allowSingletons || false,
            allowMultiple: this.props.definition.allowMultiple || true
          };
          this.onChangeAllowSingleton = this.onChangeAllowSingleton.bind(this);
          this.onChangeAllowMultiple = this.onChangeAllowMultiple.bind(this);
          this.onChangeGroupField = this.onChangeGroupField.bind(this);
          this.onChangeSorting = this.onChangeSorting.bind(this);
          this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
          this.onClose = this.onClose.bind(this);
        }

        getDefaultField() {
          return document.querySelector('#group-field').options[0].value;
        }

        renderFieldOptions() {
          const options = [];

          for (let i = 0; i < SORTED_FIELDS_AND_TITLES.length; ++i) {
            const [name, title] = SORTED_FIELDS_AND_TITLES[i];
            const permission = FIELDS_GROUP_DEF[name];

            if (permission === GroupPermission.ALL || permission === GroupPermission.ONLY_ONE && this.state.allowSingletons && !this.state.allowMultiple || permission === GroupPermission.ONLY_MANY && !this.state.allowSingletons && this.state.allowMultiple) {
              options.push( /*#__PURE__*/React.createElement("option", {
                key: i,
                value: name
              }, title));
            }
          }

          return options;
        }

        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            yes: "group",
            no: "cancel",
            onClose: this.onClose
          }, /*#__PURE__*/React.createElement("table", {
            className: "form-group"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "allow-singletons",
            checked: this.state.allowSingletons,
            onChange: this.onChangeAllowSingleton
          })), /*#__PURE__*/React.createElement("td", {
            className: "input"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "allow-singletons"
          }, "Allow singletons (groups with only 1 video)"))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "allow-multiple",
            checked: this.state.allowMultiple,
            onChange: this.onChangeAllowMultiple
          })), /*#__PURE__*/React.createElement("td", {
            className: "input"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "allow-multiple"
          }, "Allow multiple (groups with at least 2 videos)"))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-field"
          }, "Field to group (available fields depend on if singletons or multiple groups are allowed)")), /*#__PURE__*/React.createElement("td", {
            className: "input"
          }, /*#__PURE__*/React.createElement("select", {
            id: "group-field",
            value: this.state.field,
            onChange: this.onChangeGroupField
          }, this.renderFieldOptions()))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "label"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-sorting"
          }, "Sort using:")), /*#__PURE__*/React.createElement("td", {
            className: "input"
          }, /*#__PURE__*/React.createElement("select", {
            id: "group-sorting",
            value: this.state.sorting,
            onChange: this.onChangeSorting
          }, /*#__PURE__*/React.createElement("option", {
            value: "field"
          }, "Field value"), STRING_FIELDS.hasOwnProperty(this.state.field) ? /*#__PURE__*/React.createElement("option", {
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
          })), /*#__PURE__*/React.createElement("td", {
            className: "input"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-reverse"
          }, "sort in reverse order"))))));
        }

        componentDidMount() {
          if (!this.state.field) this.setState({
            field: this.getDefaultField()
          });
        }

        onChangeAllowSingleton(event) {
          this.setState({
            allowSingletons: event.target.checked,
            field: this.getDefaultField(),
            sorting: "field",
            reverse: false
          });
        }

        onChangeAllowMultiple(event) {
          this.setState({
            allowMultiple: event.target.checked,
            field: this.getDefaultField(),
            sorting: "field",
            reverse: false
          });
        }

        onChangeGroupField(event) {
          this.setState({
            field: event.target.value,
            sorting: 'field',
            reverse: false
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

        onClose(yes) {
          let definition = null;

          if (yes) {
            definition = Object.assign({}, this.state);
          }

          this.props.onClose(definition);
        }

      });
    }
  };
});