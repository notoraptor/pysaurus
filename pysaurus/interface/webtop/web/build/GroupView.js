System.register(["./constants.js"], function (_export, _context) {
  "use strict";

  var FIELD_TITLES, GroupView, Comparison;

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
    setters: [function (_constantsJs) {
      FIELD_TITLES = _constantsJs.FIELD_TITLES;
    }],
    execute: function () {
      Comparison = {
        field: compareEntryField,
        length: compareEntryFieldLength,
        count: compareEntryCount
      };

      _export("GroupView", GroupView = class GroupView extends React.Component {
        constructor(props) {
          // definition: GroupDef
          // onSelect
          super(props);
        }

        renderTitle() {
          let title = Utils.sentence(FIELD_TITLES[this.props.definition.field]);
          if (this.props.definition.sorting === "length") title = `|| ${title} ||`;else if (this.props.definition.sorting === "count") title = `${title} (#)`;
          title = `${title} ${this.props.definition.reverse ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}`;
          return title;
        }

        render() {
          const selected = this.props.definition.group_id;
          return /*#__PURE__*/React.createElement("div", {
            className: "group-view"
          }, /*#__PURE__*/React.createElement("div", {
            className: "header"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, this.renderTitle())), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.definition.groups.map((entry, index) => /*#__PURE__*/React.createElement("div", {
            className: `line ${selected === index ? 'selected' : ''}`,
            key: index,
            onClick: () => this.select(index)
          }, /*#__PURE__*/React.createElement("div", {
            className: "column left",
            title: entry.value
          }, entry.value), /*#__PURE__*/React.createElement("div", {
            className: "column right",
            title: entry.count
          }, entry.count)))));
        }

        select(value) {
          this.props.onSelect(value);
        }

      });
    }
  };
});