System.register(["../utils/constants.js", "../dialogs/FancyBox.js"], function (_export, _context) {
  "use strict";

  var SORTED_FIELDS_AND_TITLES, FancyBox, FormSort;

  _export("FormSort", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      SORTED_FIELDS_AND_TITLES = _utilsConstantsJs.SORTED_FIELDS_AND_TITLES;
    }, function (_dialogsFancyBoxJs) {
      FancyBox = _dialogsFancyBoxJs.FancyBox;
    }],
    execute: function () {
      _export("FormSort", FormSort = class FormSort extends React.Component {
        constructor(props) {
          // sorting
          // onClose(sorting)
          super(props);
          const sorting = this.props.sorting.length ? this.props.sorting : ['-date'];
          this.state = {
            sorting: sorting
          };
          this.setField = this.setField.bind(this);
          this.setReverse = this.setReverse.bind(this);
          this.addCriterion = this.addCriterion.bind(this);
          this.removeCriterion = this.removeCriterion.bind(this);
          this.submit = this.submit.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(FancyBox, {
            title: "Sort videos"
          }, /*#__PURE__*/React.createElement("div", {
            className: "form",
            id: "form-sort"
          }, /*#__PURE__*/React.createElement("div", {
            className: "help"
          }, /*#__PURE__*/React.createElement("div", null, "Click on \"+\" to add a new sorting criterion."), /*#__PURE__*/React.createElement("div", null, "Click on \"-\" to remove a sorting criterion."), /*#__PURE__*/React.createElement("div", null, "Click on \"sort\" to validate, or close dialog to cancel.")), /*#__PURE__*/React.createElement("div", {
            id: "sorting"
          }, this.renderSorting()), /*#__PURE__*/React.createElement("p", {
            className: "buttons horizontal"
          }, /*#__PURE__*/React.createElement("button", {
            className: "add",
            onClick: this.addCriterion
          }, "+"), /*#__PURE__*/React.createElement("button", {
            className: "sort",
            onClick: this.submit
          }, "sort"))));
        }

        renderSorting() {
          return this.state.sorting.map((def, index) => {
            const direction = def.charAt(0);
            const field = def.substr(1);
            const reverse = direction === "-";
            const reverseID = `reverse-${index}`;
            return /*#__PURE__*/React.createElement("p", {
              key: index,
              className: "sorting"
            }, /*#__PURE__*/React.createElement("button", {
              className: "button-remove-sort",
              onClick: () => this.removeCriterion(index)
            }, "-"), /*#__PURE__*/React.createElement("select", {
              value: field,
              onChange: event => this.setField(index, event.target.value)
            }, SORTED_FIELDS_AND_TITLES.map((entry, fieldIndex) => /*#__PURE__*/React.createElement("option", {
              key: fieldIndex,
              value: entry[0]
            }, entry[1]))), /*#__PURE__*/React.createElement("input", {
              type: "checkbox",
              id: reverseID,
              checked: reverse,
              onChange: event => this.setReverse(index, event.target.checked)
            }), /*#__PURE__*/React.createElement("label", {
              htmlFor: reverseID
            }, "reverse"));
          });
        }

        setField(index, value) {
          const sorting = this.state.sorting.slice();
          sorting[index] = `+${value}`;
          this.setState({
            sorting
          });
        }

        setReverse(index, checked) {
          const sorting = this.state.sorting.slice();
          sorting[index] = (checked ? '-' : '+') + sorting[index].substr(1);
          this.setState({
            sorting
          });
        }

        addCriterion() {
          const sorting = this.state.sorting.slice();
          sorting.push('+title');
          this.setState({
            sorting
          });
        }

        removeCriterion(index) {
          const sorting = this.state.sorting.slice();
          sorting.splice(index, 1);
          this.setState({
            sorting
          });
        }

        submit() {
          const sorting = [];

          for (let def of this.state.sorting) {
            if (sorting.indexOf(def) < 0) sorting.push(def);
          }

          Fancybox.onClose();
          this.props.onClose(sorting);
        }

      });
    }
  };
});