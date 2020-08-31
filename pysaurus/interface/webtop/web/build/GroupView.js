System.register(["./constants.js", "./buttons.js", "./Pagination.js"], function (_export, _context) {
  "use strict";

  var FIELD_TITLES, SettingIcon, Pagination, GroupView;

  function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

  _export("GroupView", void 0);

  return {
    setters: [function (_constantsJs) {
      FIELD_TITLES = _constantsJs.FIELD_TITLES;
    }, function (_buttonsJs) {
      SettingIcon = _buttonsJs.SettingIcon;
    }, function (_PaginationJs) {
      Pagination = _PaginationJs.Pagination;
    }],
    execute: function () {
      _export("GroupView", GroupView = class GroupView extends React.Component {
        constructor(props) {
          // definition: GroupDef
          // onSelect
          // onValueOptions(name, value)
          super(props);
          this.state = {
            pageSize: 100,
            pageNumber: 0
          };
          this.openPropertyOptions = this.openPropertyOptions.bind(this);
          this.setPage = this.setPage.bind(this);
        }

        getNbPages() {
          const count = this.props.definition.groups.length;
          return Math.floor(count / this.state.pageSize) + (count % this.state.pageSize ? 1 : 0);
        }

        renderTitle() {
          const field = this.props.definition.field;
          let title = field.charAt(0) === ':' ? `"${Utils.sentence(field.substr(1))}"` : Utils.sentence(FIELD_TITLES[this.props.definition.field]);
          if (this.props.definition.sorting === "length") title = `|| ${title} ||`;else if (this.props.definition.sorting === "count") title = `${title} (#)`;
          title = `${title} ${this.props.definition.reverse ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}`;
          return title;
        }

        render() {
          const selected = this.props.definition.group_id;
          const isProperty = this.props.definition.field.charAt(0) === ':';
          const start = this.state.pageSize * this.state.pageNumber;
          const end = Math.min(start + this.state.pageSize, this.props.definition.groups.length);
          console.log(`Rendering ${this.props.definition.groups.length} group(s).`);
          return /*#__PURE__*/React.createElement("div", {
            className: "group-view"
          }, /*#__PURE__*/React.createElement("div", {
            className: "header"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, this.renderTitle()), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Pagination, {
            singular: "page",
            plural: "pages",
            nbPages: this.getNbPages(),
            pageNumber: this.state.pageNumber,
            key: this.state.pageNumber,
            onChange: this.setPage
          }))), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.definition.groups.slice(start, end).map((entry, index) => /*#__PURE__*/React.createElement("div", {
            className: `line ${selected === index ? 'selected' : ''} ${isProperty ? 'property' : 'attribute'} ${entry.value === null ? 'all' : ''}`,
            key: index,
            onClick: () => this.select(start + index)
          }, /*#__PURE__*/React.createElement("div", _extends({
            className: "column left"
          }, isProperty ? {} : {
            title: entry.value
          }), isProperty && entry.value !== null ? [/*#__PURE__*/React.createElement(SettingIcon, {
            key: "options",
            title: `Options ...`,
            action: () => this.openPropertyOptions(index)
          }), '  '] : '', /*#__PURE__*/React.createElement("span", _extends({
            key: "value"
          }, isProperty ? {
            title: entry.value
          } : {}), entry.value === null ? `(none)` : entry.value)), /*#__PURE__*/React.createElement("div", {
            className: "column right",
            title: entry.count
          }, entry.count)))));
        }

        select(value) {
          this.props.onSelect(value);
        }

        openPropertyOptions(index) {
          this.props.onValueOptions(this.props.definition.field.substr(1), this.props.definition.groups[index].value);
        }

        setPage(pageNumber) {
          this.setState({
            pageNumber
          });
        }

      });
    }
  };
});