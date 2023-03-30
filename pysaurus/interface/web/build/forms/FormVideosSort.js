System.register(["../utils/constants.js", "../dialogs/FancyBox.js", "../language.js", "../utils/FancyboxManager.js"], function (_export, _context) {
  "use strict";

  var FIELD_MAP, FancyBox, LangContext, tr, Fancybox, FormVideosSort;
  _export("FormVideosSort", void 0);
  return {
    setters: [function (_utilsConstantsJs) {
      FIELD_MAP = _utilsConstantsJs.FIELD_MAP;
    }, function (_dialogsFancyBoxJs) {
      FancyBox = _dialogsFancyBoxJs.FancyBox;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
      tr = _languageJs.tr;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }],
    execute: function () {
      _export("FormVideosSort", FormVideosSort = class FormVideosSort extends React.Component {
        constructor(props) {
          // sorting
          // onClose(sorting)
          super(props);
          const sorting = this.props.sorting.length ? this.props.sorting : ["-date"];
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
            title: tr("Sort videos")
          }, /*#__PURE__*/React.createElement("div", {
            id: "form-videos-sort",
            className: "form absolute-plain vertical text-center p-2"
          }, /*#__PURE__*/React.createElement("div", {
            className: "help mb-4"
          }, tr(`
Click on "+" to add a new sorting criterion.

Click on "-" to remove a sorting criterion.

Click on "sort" to validate, or close dialog to cancel.
`, null, "markdown")), /*#__PURE__*/React.createElement("div", {
            id: "sorting",
            className: "flex-grow-1 overflow-auto"
          }, this.renderSorting()), /*#__PURE__*/React.createElement("p", {
            className: "buttons flex-shrink-0 horizontal"
          }, /*#__PURE__*/React.createElement("button", {
            className: "add flex-grow-1 mr-1",
            onClick: this.addCriterion
          }, "+"), /*#__PURE__*/React.createElement("button", {
            className: "sort flex-grow-1 ml-2",
            onClick: this.submit
          }, /*#__PURE__*/React.createElement("strong", null, "sort")))));
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
            }, FIELD_MAP.sortable.map((entry, fieldIndex) => /*#__PURE__*/React.createElement("option", {
              key: fieldIndex,
              value: entry.name
            }, entry.title))), /*#__PURE__*/React.createElement("input", {
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
          sorting[index] = (checked ? "-" : "+") + sorting[index].substr(1);
          this.setState({
            sorting
          });
        }
        addCriterion() {
          const sorting = this.state.sorting.slice();
          sorting.push("+title");
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
          Fancybox.close();
          if (sorting.length) this.props.onClose(sorting);
        }
      });
      FormVideosSort.contextType = LangContext;
    }
  };
});