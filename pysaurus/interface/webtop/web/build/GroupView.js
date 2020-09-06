System.register(["./constants.js", "./buttons.js", "./Pagination.js"], function (_export, _context) {
  "use strict";

  var FIELD_TITLES, SettingIcon, PlusIcon, Pagination, GroupView;

  function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

  _export("GroupView", void 0);

  return {
    setters: [function (_constantsJs) {
      FIELD_TITLES = _constantsJs.FIELD_TITLES;
    }, function (_buttonsJs) {
      SettingIcon = _buttonsJs.SettingIcon;
      PlusIcon = _buttonsJs.PlusIcon;
    }, function (_PaginationJs) {
      Pagination = _PaginationJs.Pagination;
    }],
    execute: function () {
      _export("GroupView", GroupView = class GroupView extends React.Component {
        constructor(props) {
          /*
          groupID
          field
          sorting
          reverse
          groups
          onSelect(index)
          onOptions? callback(index)
          onPlus? callback(index)
          */
          super(props);
          this.state = {
            pageSize: 100,
            pageNumber: 0
          };
          this.openPropertyOptions = this.openPropertyOptions.bind(this);
          this.openPropertyPlus = this.openPropertyPlus.bind(this);
          this.setPage = this.setPage.bind(this);
          this.search = this.search.bind(this);
        }

        render() {
          const selected = this.props.groupID;
          const isProperty = this.props.field.charAt(0) === ':';
          const start = this.state.pageSize * this.state.pageNumber;
          const end = Math.min(start + this.state.pageSize, this.props.groups.length);
          console.log(`Rendering ${this.props.groups.length} group(s).`);
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
            onChange: this.setPage,
            onSearch: this.search
          }))), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.groups.slice(start, end).map((entry, index) => {
            index = start + index;
            const buttons = [];

            if (isProperty && entry.value !== null) {
              if (this.props.onOptions) {
                buttons.push( /*#__PURE__*/React.createElement(SettingIcon, {
                  key: "options",
                  title: `Options ...`,
                  action: event => this.openPropertyOptions(event, index)
                }));
                buttons.push(' ');
              }

              if (this.props.onPlus) {
                buttons.push( /*#__PURE__*/React.createElement(PlusIcon, {
                  key: "add",
                  title: `Add ...`,
                  action: event => this.openPropertyPlus(event, index)
                }));
                buttons.push(' ');
              }
            }

            return /*#__PURE__*/React.createElement("div", {
              className: `line ${selected === index ? 'selected' : ''} ${isProperty ? 'property' : 'attribute'} ${entry.value === null ? 'all' : ''}`,
              key: index,
              onClick: () => this.select(index)
            }, /*#__PURE__*/React.createElement("div", _extends({
              className: "column left"
            }, isProperty ? {} : {
              title: entry.value
            }), buttons, /*#__PURE__*/React.createElement("span", _extends({
              key: "value"
            }, isProperty ? {
              title: entry.value
            } : {}), entry.value === null ? `(none)` : entry.value)), /*#__PURE__*/React.createElement("div", {
              className: "column right",
              title: entry.count
            }, entry.count));
          })));
        }

        renderTitle() {
          const field = this.props.field;
          let title = field.charAt(0) === ':' ? `"${Utils.sentence(field.substr(1))}"` : Utils.sentence(FIELD_TITLES[field]);
          if (this.props.sorting === "length") title = `|| ${title} ||`;else if (this.props.sorting === "count") title = `${title} (#)`;
          title = `${title} ${this.props.reverse ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}`;
          return title;
        }

        getNbPages() {
          const count = this.props.groups.length;
          return Math.floor(count / this.state.pageSize) + (count % this.state.pageSize ? 1 : 0);
        }

        select(value) {
          this.props.onSelect(value);
        }

        openPropertyOptions(event, index) {
          event.cancelBubble = true;
          event.stopPropagation();
          this.props.onOptions(index);
        }

        openPropertyPlus(event, index) {
          event.cancelBubble = true;
          event.stopPropagation();
          this.props.onPlus(index);
        }

        setPage(pageNumber) {
          this.setState({
            pageNumber
          });
        }

        search(text) {
          for (let index = 0; index < this.props.groups.length; ++index) {
            const value = this.props.groups[index].value;
            if (value === null) continue;
            if (value.toString().toLowerCase().indexOf(text.trim().toLowerCase()) !== 0) continue;
            const pageNumber = Math.floor(index / this.state.pageSize);
            this.setState({
              pageNumber
            }, () => this.select(index));
            return;
          }
        }

      });
    }
  };
});