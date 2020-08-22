System.register(["./constants.js"], function (_export, _context) {
  "use strict";

  var SORTED_FIELDS_AND_TITLES, FormGroup, REVERSE_VALUES;

  _export("FormGroup", void 0);

  return {
    setters: [function (_constantsJs) {
      SORTED_FIELDS_AND_TITLES = _constantsJs.SORTED_FIELDS_AND_TITLES;
    }],
    execute: function () {
      REVERSE_VALUES = {
        "true": true,
        "false": false
      };

      _export("FormGroup", FormGroup = class FormGroup extends React.Component {
        constructor(props) {
          // field
          // reverse
          // onClose
          super(props);
          this.state = {
            field: this.props.field || '',
            reverse: this.props.reverse || ''
          };
          this.onChangeGroupField = this.onChangeGroupField.bind(this);
          this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "form-group"
          }, /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("select", {
            id: "group-field",
            name: "groupField",
            value: this.state.field,
            onChange: this.onChangeGroupField
          }, SORTED_FIELDS_AND_TITLES.map((entry, fieldIndex) => /*#__PURE__*/React.createElement("option", {
            key: fieldIndex,
            value: entry[0]
          }, entry[1])))), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "group-reverse-off",
            name: "groupReverse",
            value: false,
            checked: this.state.reverse === false,
            onChange: this.onChangeGroupReverse
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-reverse-off"
          }, " ascending")), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "group-reverse-on",
            name: "groupReverse",
            value: true,
            checked: this.state.reverse === true,
            onChange: this.onChangeGroupReverse
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-reverse-on"
          }, " descending")));
        }

        onChangeGroupField(event) {
          this.setState({
            field: event.target.value,
            reverse: ''
          });
        }

        onChangeGroupReverse(event) {
          const field = this.state.field || document.querySelector('#group-field').value;
          const reverse = REVERSE_VALUES[event.target.value];
          this.setState({
            reverse
          }, () => this.props.onClose({
            field,
            reverse
          }));
        }

      });
    }
  };
});