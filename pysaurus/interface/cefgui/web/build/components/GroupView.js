System.register(["../utils/constants.js", "./Pagination.js", "./SettingIcon.js", "./PlusIcon.js", "../utils/functions.js", "../utils/Actions.js", "../utils/Action.js"], function (_export, _context) {
  "use strict";

  var Characters, FIELD_MAP, Pagination, SettingIcon, PlusIcon, capitalizeFirstLetter, Actions, Action, GroupView;

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
    }, function (_utilsActionsJs) {
      Actions = _utilsActionsJs.Actions;
    }, function (_utilsActionJs) {
      Action = _utilsActionJs.Action;
    }],
    execute: function () {
      _export("GroupView", GroupView = class GroupView extends React.Component {
        constructor(props) {
          super(props);
          this.openPropertyOptions = this.openPropertyOptions.bind(this);
          this.openPropertyOptionsAll = this.openPropertyOptionsAll.bind(this);
          this.openPropertyPlus = this.openPropertyPlus.bind(this);
          this.setPage = this.setPage.bind(this);
          this.previousGroup = this.previousGroup.bind(this);
          this.nextGroup = this.nextGroup.bind(this);
          this.search = this.search.bind(this);
          this.allChecked = this.allChecked.bind(this);
          this.onCheckEntry = this.onCheckEntry.bind(this);
          this.onCheckAll = this.onCheckAll.bind(this);
          this.callbackIndex = -1;
          this.features = new Actions({
            previous: new Action("Ctrl+ArrowUp", "Go to previous group", this.previousGroup),
            next: new Action("Ctrl+ArrowDown", "Go to next group", this.nextGroup)
          });
        }

        render() {
          const selection = this.props.selection;
          const selected = this.props.groupDef.group_id;
          const isProperty = this.props.groupDef.is_property;
          const start = this.props.pageSize * this.props.pageNumber;
          const end = Math.min(start + this.props.pageSize, this.props.groupDef.groups.length);
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
            pageNumber: this.props.pageNumber,
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
          }, allChecked ? 'All ' : '', selection.size, " selected"), selection.size ? /*#__PURE__*/React.createElement("span", null, "\xA0", /*#__PURE__*/React.createElement(SettingIcon, {
            key: "options-for-selected",
            title: `Options for selected...`,
            action: this.openPropertyOptionsAll
          })) : '')) : ''), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, this.props.groupDef.groups.length ? /*#__PURE__*/React.createElement("table", {
            className: "second-td-text-right"
          }, this.props.groupDef.groups.slice(start, end).map((entry, index) => {
            index = start + index;
            const buttons = [];

            if (isProperty && entry.value !== null) {
              if (!this.props.isClassified) {
                buttons.push( /*#__PURE__*/React.createElement("input", {
                  type: "checkbox",
                  checked: selection.has(index),
                  onChange: event => this.onCheckEntry(event, index)
                }));
                buttons.push(' ');

                if (!selection.size) {
                  buttons.push( /*#__PURE__*/React.createElement(SettingIcon, {
                    key: "options",
                    title: `Options ...`,
                    action: event => this.openPropertyOptions(event, index)
                  }));
                  buttons.push(' ');
                }
              }

              if (!selection.size) {
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
              onClick: () => this.props.onGroupViewState({
                groupID: index
              })
            }, /*#__PURE__*/React.createElement("td", isProperty ? {} : {
              title: entry.value
            }, buttons, /*#__PURE__*/React.createElement("span", _extends({
              key: "value"
            }, isProperty ? {
              title: entry.value
            } : {}), entry.value === null ? `(none)` : entry.value)), /*#__PURE__*/React.createElement("td", {
              title: entry.count
            }, entry.count));
          })) : /*#__PURE__*/React.createElement("div", {
            className: "absolute-plain no-groups vertical"
          }, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, "No groups")))));
        }

        renderTitle() {
          const field = this.props.groupDef.field;
          let title = this.props.groupDef.is_property ? `"${capitalizeFirstLetter(field)}"` : capitalizeFirstLetter(FIELD_MAP.fields[field].title);
          if (this.props.groupDef.sorting === "length") title = `|| ${title} ||`;else if (this.props.groupDef.sorting === "count") title = `${title} (#)`;
          title = `${title} ${this.props.groupDef.reverse ? Characters.ARROW_DOWN : Characters.ARROW_UP}`;
          return title;
        }

        componentDidMount() {
          this.callbackIndex = KEYBOARD_MANAGER.register(this.features.onKeyPressed);
        }

        componentWillUnmount() {
          KEYBOARD_MANAGER.unregister(this.callbackIndex);
        }

        getNullIndex() {
          return this.props.groupDef.groups.length && this.props.groupDef.groups[0].value === null ? 0 : -1;
        }

        getNbPages() {
          const count = this.props.groupDef.groups.length;
          return Math.floor(count / this.props.pageSize) + (count % this.props.pageSize ? 1 : 0);
        }

        openPropertyOptions(event, index) {
          event.cancelBubble = true;
          event.stopPropagation();
          this.props.onOptions(new Set([index]));
        }

        openPropertyOptionsAll() {
          this.props.onOptions(this.props.selection);
        }

        openPropertyPlus(event, index) {
          event.cancelBubble = true;
          event.stopPropagation();
          if (this.props.onPlus) this.props.onPlus(index);
        }

        setPage(pageNumber) {
          if (this.props.pageNumber !== pageNumber) this.props.onGroupViewState({
            pageNumber: pageNumber,
            selection: new Set()
          });
        }

        previousGroup() {
          const groupID = this.props.groupDef.group_id;
          if (groupID > 0) this.props.onGroupViewState({
            groupID: groupID - 1
          });
        }

        nextGroup() {
          const groupID = this.props.groupDef.group_id;
          if (groupID < this.props.groupDef.groups.length - 1) this.props.onGroupViewState({
            groupID: groupID + 1
          });
        }

        search(text) {
          for (let index = 0; index < this.props.groupDef.groups.length; ++index) {
            const value = this.props.groupDef.groups[index].value;
            if (value === null) continue;
            if (value.toString().toLowerCase().indexOf(text.trim().toLowerCase()) !== 0) continue;
            const pageNumber = Math.floor(index / this.props.pageSize);
            if (this.props.pageNumber !== pageNumber) this.props.onGroupViewState({
              pageNumber: pageNumber,
              selection: new Set(),
              groupID: index
            });
            return;
          }
        }

        allChecked(start, end) {
          const nullGroupIndex = this.getNullIndex();

          for (let i = start; i < end; ++i) {
            if (!this.props.selection.has(i) && i !== nullGroupIndex) return false;
          }

          return true;
        }

        onCheckEntry(event, index) {
          const selection = new Set(this.props.selection);

          if (event.target.checked) {
            selection.add(index);
          } else {
            selection.delete(index);
          }

          this.props.onGroupViewState({
            selection
          });
        }

        onCheckAll(event, start, end) {
          const selection = new Set(this.props.selection);

          if (event.target.checked) {
            for (let i = start; i < end; ++i) {
              selection.add(i);
            }
          } else {
            for (let i = start; i < end; ++i) {
              selection.delete(i);
            }
          }

          selection.delete(this.getNullIndex());
          this.props.onGroupViewState({
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
        // onOptions(index)
        onOptions: PropTypes.func.isRequired,
        // onPlus(index)
        onPlus: PropTypes.func,
        // state
        pageSize: PropTypes.number.isRequired,
        pageNumber: PropTypes.number.isRequired,
        selection: PropTypes.instanceOf(Set).isRequired,
        // state change
        onGroupViewState: PropTypes.func.isRequired // onGroupViewState({pageSize?, pageNumber?, selection?, groupID? => onSelect})

      };
    }
  };
});