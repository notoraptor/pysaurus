System.register(["../utils/constants.js", "./Pagination.js", "./SettingIcon.js", "./PlusIcon.js", "../utils/functions.js"], function (_export, _context) {
  "use strict";

  var Characters, FIELD_MAP, Pagination, SettingIcon, PlusIcon, capitalizeFirstLetter, GroupView;

  function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

  _export("GroupView", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
      FIELD_MAP = _utilsConstantsJs.FIELD_MAP;
    }, function (_PaginationJs) {
      Pagination = _PaginationJs.Pagination;
    }, function (_SettingIconJs) {
      SettingIcon = _SettingIconJs.SettingIcon;
    }, function (_PlusIconJs) {
      PlusIcon = _PlusIconJs.PlusIcon;
    }, function (_utilsFunctionsJs) {
      capitalizeFirstLetter = _utilsFunctionsJs.capitalizeFirstLetter;
    }],
    execute: function () {
      _export("GroupView", GroupView = class GroupView extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            pageSize: 100,
            pageNumber: 0,
            selection: new Set()
          };
          this.openPropertyOptions = this.openPropertyOptions.bind(this);
          this.openPropertyOptionsAll = this.openPropertyOptionsAll.bind(this);
          this.openPropertyPlus = this.openPropertyPlus.bind(this);
          this.setPage = this.setPage.bind(this);
          this.search = this.search.bind(this);
          this.allChecked = this.allChecked.bind(this);
          this.onCheckEntry = this.onCheckEntry.bind(this);
          this.onCheckAll = this.onCheckAll.bind(this);
          this.nullIndex = -1;

          for (let i = 0; i < this.props.groupDef.groups.length; ++i) {
            if (this.props.groupDef.groups[i].value === null) {
              if (i !== 0) throw `Group without value at position ${i}, expected 0`;
              this.nullIndex = i;
              break;
            }
          }
        }

        render() {
          const selected = this.props.groupDef.group_id;
          const isProperty = this.props.groupDef.is_property;
          const start = this.state.pageSize * this.state.pageNumber;
          const end = Math.min(start + this.state.pageSize, this.props.groupDef.groups.length);
          const allChecked = this.allChecked(start, end);
          console.log(`Rendering ${this.props.groupDef.groups.length} group(s).`);
          return /*#__PURE__*/React.createElement("div", {
            className: "group-view vertical"
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
          })), isProperty && !this.props.isClassified ? /*#__PURE__*/React.createElement("div", {
            className: "selection line horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "column"
          }, /*#__PURE__*/React.createElement("input", {
            id: "group-view-select-all",
            type: "checkbox",
            checked: allChecked,
            onChange: event => this.onCheckAll(event, start, end)
          }), ' ', /*#__PURE__*/React.createElement("label", {
            htmlFor: "group-view-select-all"
          }, allChecked ? 'All ' : '', this.state.selection.size, " selected"), this.state.selection.size ? /*#__PURE__*/React.createElement("span", null, "\xA0", /*#__PURE__*/React.createElement(SettingIcon, {
            key: "options-for-selected",
            title: `Options for selected...`,
            action: this.openPropertyOptionsAll
          })) : '')) : ''), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, /*#__PURE__*/React.createElement("table", {
            className: "second-td-text-right"
          }, this.props.groupDef.groups.slice(start, end).map((entry, index) => {
            index = start + index;
            const buttons = [];

            if (isProperty && entry.value !== null) {
              if (!this.props.isClassified) {
                buttons.push( /*#__PURE__*/React.createElement("input", {
                  type: "checkbox",
                  checked: this.state.selection.has(index),
                  onChange: event => this.onCheckEntry(event, index)
                }));
                buttons.push(' ');

                if (!this.state.selection.size) {
                  buttons.push( /*#__PURE__*/React.createElement(SettingIcon, {
                    key: "options",
                    title: `Options ...`,
                    action: event => this.openPropertyOptions(event, index)
                  }));
                  buttons.push(' ');
                }
              }

              if (!this.state.selection.size) {
                buttons.push( /*#__PURE__*/React.createElement(PlusIcon, {
                  key: "add",
                  title: `Add ...`,
                  action: event => this.openPropertyPlus(event, index)
                }));
                buttons.push(' ');
              }
            }

            const classes = [isProperty ? "property" : "attribute"];
            if (selected === index) classes.push("selected");
            if (entry.value === null) classes.push("all");
            return /*#__PURE__*/React.createElement("tr", {
              className: classes.join(" "),
              key: index,
              onClick: () => this.props.onSelect(index)
            }, /*#__PURE__*/React.createElement("td", isProperty ? {} : {
              title: entry.value
            }, buttons, /*#__PURE__*/React.createElement("span", _extends({
              key: "value"
            }, isProperty ? {
              title: entry.value
            } : {}), entry.value === null ? `(none)` : entry.value)), /*#__PURE__*/React.createElement("td", {
              title: entry.count
            }, entry.count));
          }))));
        }

        renderTitle() {
          const field = this.props.groupDef.field;
          let title = this.props.groupDef.is_property ? `"${capitalizeFirstLetter(field)}"` : capitalizeFirstLetter(FIELD_MAP.fields[field].title);
          if (this.props.groupDef.sorting === "length") title = `|| ${title} ||`;else if (this.props.groupDef.sorting === "count") title = `${title} (#)`;
          title = `${title} ${this.props.groupDef.reverse ? Characters.ARROW_DOWN : Characters.ARROW_UP}`;
          return title;
        }

        getNbPages() {
          const count = this.props.groupDef.groups.length;
          return Math.floor(count / this.state.pageSize) + (count % this.state.pageSize ? 1 : 0);
        }

        openPropertyOptions(event, index) {
          event.cancelBubble = true;
          event.stopPropagation();
          this.props.onOptions(new Set([index]));
        }

        openPropertyOptionsAll() {
          this.props.onOptions(this.state.selection);
        }

        openPropertyPlus(event, index) {
          event.cancelBubble = true;
          event.stopPropagation();
          if (this.props.onPlus) this.props.onPlus(index);
        }

        setPage(pageNumber) {
          if (this.state.pageNumber !== pageNumber) this.setState({
            pageNumber: pageNumber,
            selection: new Set()
          });
        }

        search(text) {
          for (let index = 0; index < this.props.groupDef.groups.length; ++index) {
            const value = this.props.groupDef.groups[index].value;
            if (value === null) continue;
            if (value.toString().toLowerCase().indexOf(text.trim().toLowerCase()) !== 0) continue;
            const pageNumber = Math.floor(index / this.state.pageSize);
            if (this.state.pageNumber !== pageNumber) this.setState({
              pageNumber: pageNumber,
              selection: new Set()
            }, () => this.props.onSelect(index));
            return;
          }
        }

        allChecked(start, end) {
          for (let i = start; i < end; ++i) {
            if (!this.state.selection.has(i) && i !== this.nullIndex) return false;
          }

          return true;
        }

        onCheckEntry(event, index) {
          const selection = new Set(this.state.selection);

          if (event.target.checked) {
            selection.add(index);
          } else {
            selection.delete(index);
          }

          this.setState({
            selection
          });
        }

        onCheckAll(event, start, end) {
          const selection = new Set(this.state.selection);

          if (event.target.checked) {
            for (let i = start; i < end; ++i) {
              selection.add(i);
            }
          } else {
            for (let i = start; i < end; ++i) {
              selection.delete(i);
            }
          }

          selection.delete(this.nullIndex);
          this.setState({
            selection
          });
        }

      });

      GroupView.propTypes = {
        groupDef: PropTypes.shape({
          group_id: PropTypes.number.isRequired,
          field: PropTypes.string.isRequired,
          is_property: PropTypes.bool.isRequired,
          sorting: PropTypes.string.isRequired,
          reverse: PropTypes.bool.isRequired,
          groups: PropTypes.arrayOf(PropTypes.shape({
            value: PropTypes.any,
            count: PropTypes.number
          })).isRequired
        }).isRequired,
        isClassified: PropTypes.bool.isRequired,
        // onSelect(index)
        onSelect: PropTypes.func.isRequired,
        // onOptions(index)
        onOptions: PropTypes.func.isRequired,
        // onPlus(index)
        onPlus: PropTypes.func
      };
    }
  };
});