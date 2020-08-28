System.register([], function (_export, _context) {
  "use strict";

  var GroupView, Comparison;

  function applyReverse(value, reverse) {
    return reverse ? -value : value;
  }

  function compareString(a, b) {
    let t = a.toLowerCase().localeCompare(b.toLowerCase());
    if (t === 0) t = a.localeCompare(b);
    return t;
  }

  function compareEntryCount(entry1, entry2, reverse) {
    let t = applyReverse(entry1[1] - entry2[1], reverse);
    if (t === 0) t = compareString(entry1[0], entry2[0]);
    return t;
  }

  function compareEntryField(entry1, entry2, reverse) {
    let t = applyReverse(compareString(entry1[0], entry2[0]), reverse);
    if (t === 0) t = entry1[1] - entry2[1];
    return t;
  }

  function compareEntryFieldLength(entry1, entry2, reverse) {
    let t = applyReverse(entry1[0].length - entry2[0].length, reverse);
    if (t === 0) t = compareEntryField(entry1, entry2, reverse);
    return t;
  }

  _export("GroupView", void 0);

  return {
    setters: [],
    execute: function () {
      Comparison = {
        field: compareEntryField,
        length: compareEntryFieldLength,
        count: compareEntryCount
      };

      _export("GroupView", GroupView = class GroupView extends React.Component {
        constructor(props) {
          // title: str
          // isString: true
          // groups: {<value> : <count>}
          // all? int
          super(props);
          this.state = {
            sorting: "field",
            reverse: false,
            data: []
          };
          this.state.data = this.sort(this.state.sorting, this.state.reverse);
          this.sort = this.sort.bind(this);
          this.changeSorting = this.changeSorting.bind(this);
          this.changeReverse = this.changeReverse.bind(this);
          this.switchReverse = this.switchReverse.bind(this);
        }

        sort(sorting, reverse) {
          const data = Object.entries(this.props.groups);
          data.sort((a, b) => Comparison[sorting](a, b, reverse));
          return data;
        }

        changeSorting(event) {
          const sorting = event.target.value;
          const reverse = false;
          const data = this.sort(sorting, reverse);
          this.setState({
            sorting,
            reverse,
            data
          });
        }

        changeReverse(event) {
          const reverse = event.target.checked;
          const data = this.sort(this.state.sorting, reverse);
          this.setState({
            reverse,
            data
          });
        }

        switchReverse() {
          const reverse = !this.state.reverse;
          const data = this.sort(this.state.sorting, reverse);
          this.setState({
            reverse,
            data
          });
        }

        renderReverse() {
          return this.state.reverse ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP;
        }

        render() {
          const title = Utils.sentence(this.props.title);
          return /*#__PURE__*/React.createElement("div", {
            className: "group-view"
          }, /*#__PURE__*/React.createElement("div", {
            className: "header"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, title), /*#__PURE__*/React.createElement("div", {
            className: "form"
          }, /*#__PURE__*/React.createElement("select", {
            value: this.state.sorting,
            onChange: this.changeSorting
          }, /*#__PURE__*/React.createElement("option", {
            value: "field"
          }, title), this.props.isString ? /*#__PURE__*/React.createElement("option", {
            value: "length"
          }, "|| ", title, " ||") : '', /*#__PURE__*/React.createElement("option", {
            value: "count"
          }, "#")), /*#__PURE__*/React.createElement("button", {
            onClick: this.switchReverse
          }, this.renderReverse()))), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.all !== undefined ? /*#__PURE__*/React.createElement("div", {
            className: "line all"
          }, /*#__PURE__*/React.createElement("div", {
            className: "column left",
            title: "(all)"
          }, "(all)"), /*#__PURE__*/React.createElement("div", {
            className: "column right",
            title: this.props.all
          }, this.props.all)) : '', this.state.data.map((entry, index) => /*#__PURE__*/React.createElement("div", {
            className: "line",
            key: index
          }, /*#__PURE__*/React.createElement("div", {
            className: "column left",
            title: entry[0]
          }, entry[0]), /*#__PURE__*/React.createElement("div", {
            className: "column right",
            title: entry[1]
          }, entry[1])))));
        }

      });
    }
  };
});