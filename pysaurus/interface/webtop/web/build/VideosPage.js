System.register(["./buttons.js", "./constants.js", "./MenuPack.js", "./Pagination.js", "./Video.js", "./FormSourceVideo.js", "./FormGroup.js", "./FormSearch.js", "./FormSort.js", "./GroupView.js", "./Dialog.js", "./Cell.js", "./FormEditPropertyValue.js", "./FormSetClassification.js", "./FormFillKeywords.js"], function (_export, _context) {
  "use strict";

  var SettingIcon, Cross, PAGE_SIZES, FIELDS, SEARCH_TYPE_TITLE, MenuPack, MenuItem, Menu, MenuItemCheck, Pagination, Video, FormSourceVideo, FormGroup, FormSearch, FormSort, GroupView, Dialog, Cell, FormEditPropertyValue, FormSetClassification, FormFillKeywords, Filter, VideosPage, SHORTCUTS, SPECIAL_KEYS;

  function assertUniqueShortcuts() {
    const duplicates = {};

    for (let key of Object.keys(SHORTCUTS)) {
      const value = SHORTCUTS[key];
      if (duplicates.hasOwnProperty(value)) throw new Error(`Duplicated shortcut ${value} for ${duplicates[value]} and ${key}.`);
      duplicates[value] = key;
    }
  }

  /**
   * @param event {KeyboardEvent}
   * @param shortcut {string}
   */
  function shortcutPressed(event, shortcut) {
    const pieces = shortcut.split('+');
    if (!pieces.length) return false;
    if (event.key.toLowerCase() !== pieces[pieces.length - 1].toLowerCase()) return false;

    for (let i = 0; i < pieces.length - 1; ++i) {
      const key = pieces[i].toLowerCase();
      if (!SPECIAL_KEYS.hasOwnProperty(key) || !event[SPECIAL_KEYS[key]]) return false;
    }

    return true;
  }

  _export("VideosPage", void 0);

  return {
    setters: [function (_buttonsJs) {
      SettingIcon = _buttonsJs.SettingIcon;
      Cross = _buttonsJs.Cross;
    }, function (_constantsJs) {
      PAGE_SIZES = _constantsJs.PAGE_SIZES;
      FIELDS = _constantsJs.FIELDS;
      SEARCH_TYPE_TITLE = _constantsJs.SEARCH_TYPE_TITLE;
    }, function (_MenuPackJs) {
      MenuPack = _MenuPackJs.MenuPack;
      MenuItem = _MenuPackJs.MenuItem;
      Menu = _MenuPackJs.Menu;
      MenuItemCheck = _MenuPackJs.MenuItemCheck;
    }, function (_PaginationJs) {
      Pagination = _PaginationJs.Pagination;
    }, function (_VideoJs) {
      Video = _VideoJs.Video;
    }, function (_FormSourceVideoJs) {
      FormSourceVideo = _FormSourceVideoJs.FormSourceVideo;
    }, function (_FormGroupJs) {
      FormGroup = _FormGroupJs.FormGroup;
    }, function (_FormSearchJs) {
      FormSearch = _FormSearchJs.FormSearch;
    }, function (_FormSortJs) {
      FormSort = _FormSortJs.FormSort;
    }, function (_GroupViewJs) {
      GroupView = _GroupViewJs.GroupView;
    }, function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }, function (_CellJs) {
      Cell = _CellJs.Cell;
    }, function (_FormEditPropertyValueJs) {
      FormEditPropertyValue = _FormEditPropertyValueJs.FormEditPropertyValue;
    }, function (_FormSetClassificationJs) {
      FormSetClassification = _FormSetClassificationJs.FormSetClassification;
    }, function (_FormFillKeywordsJs) {
      FormFillKeywords = _FormFillKeywordsJs.FormFillKeywords;
    }],
    execute: function () {
      SHORTCUTS = {
        select: "Ctrl+T",
        group: "Ctrl+G",
        search: "Ctrl+F",
        sort: "Ctrl+S",
        reload: "Ctrl+R",
        manageProperties: "Ctrl+P"
      };
      SPECIAL_KEYS = {
        ctrl: "ctrlKey",
        alt: "altKey",
        shift: "shiftKey",
        maj: "shiftKey"
      };
      assertUniqueShortcuts();
      Filter = class Filter extends React.Component {
        constructor(props) {
          // page: VideosPage
          super(props);
        }

        render() {
          const app = this.props.page;
          const backend = app.state;
          const sources = backend.sources;
          const groupDef = backend.groupDef;
          const searchDef = backend.searchDef;
          const sorting = backend.sorting;
          const sortingIsDefault = sorting.length === 1 && sorting[0] === '-date';
          return /*#__PURE__*/React.createElement("table", {
            className: "filter"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, sources.map((source, index) => /*#__PURE__*/React.createElement("div", {
            key: index
          }, source.join(' ').replace('_', ' ')))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement(SettingIcon, {
            title: `Select sources ... (${SHORTCUTS.select})`,
            action: app.selectVideos
          }))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, groupDef ? /*#__PURE__*/React.createElement("div", null, "Grouped") : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, "Ungrouped")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SettingIcon, {
            title: (groupDef ? 'Edit ...' : 'Group ...') + ` (${SHORTCUTS.group})`,
            action: app.groupVideos
          })), groupDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Cross, {
            title: "Reset group",
            action: app.resetGroup
          })) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, "Searched ", SEARCH_TYPE_TITLE[searchDef.cond]), /*#__PURE__*/React.createElement("div", null, "\"", /*#__PURE__*/React.createElement("strong", null, searchDef.text), "\"")) : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, "No search")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SettingIcon, {
            title: (searchDef ? 'Edit ...' : 'Search ...') + ` (${SHORTCUTS.search})`,
            action: app.searchVideos
          })), searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Cross, {
            title: "reset search",
            action: app.resetSearch
          })) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, "Sorted by"), sorting.map((val, i) => /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, val.substr(1)), ' ', val[0] === '-' ? /*#__PURE__*/React.createElement("span", null, "\u25BC") : /*#__PURE__*/React.createElement("span", null, "\u25B2")))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SettingIcon, {
            title: `Sort ... (${SHORTCUTS.sort})`,
            action: app.sortVideos
          })), sortingIsDefault ? '' : /*#__PURE__*/React.createElement(Cross, {
            title: "reset sorting",
            action: app.resetSort
          })))));
        }

      };

      _export("VideosPage", VideosPage = class VideosPage extends React.Component {
        constructor(props) {
          // parameters: {pageSize, pageNumber, info}
          // app: App
          super(props);
          this.state = {
            status: 'Loaded.',
            confirmDeletion: true,
            stackFilter: false,
            stackGroup: false
          };
          this.parametersToState = this.parametersToState.bind(this);
          this.checkShortcut = this.checkShortcut.bind(this);
          this.changeGroup = this.changeGroup.bind(this);
          this.changePage = this.changePage.bind(this);
          this.confirmDeletionForNotFound = this.confirmDeletionForNotFound.bind(this);
          this.groupVideos = this.groupVideos.bind(this);
          this.manageProperties = this.manageProperties.bind(this);
          this.openRandomVideo = this.openRandomVideo.bind(this);
          this.reloadDatabase = this.reloadDatabase.bind(this);
          this.resetGroup = this.resetGroup.bind(this);
          this.resetSearch = this.resetSearch.bind(this);
          this.resetSort = this.resetSort.bind(this);
          this.searchVideos = this.searchVideos.bind(this);
          this.selectVideos = this.selectVideos.bind(this);
          this.setPageSize = this.setPageSize.bind(this);
          this.sortVideos = this.sortVideos.bind(this);
          this.updateStatus = this.updateStatus.bind(this);
          this.resetStatus = this.resetStatus.bind(this);
          this.scrollTop = this.scrollTop.bind(this);
          this.stackGroup = this.stackGroup.bind(this);
          this.stackFilter = this.stackFilter.bind(this);
          this.selectGroup = this.selectGroup.bind(this);
          this.editPropertyValue = this.editPropertyValue.bind(this);
          this.classify = this.classify.bind(this);
          this.fillWithKeywords = this.fillWithKeywords.bind(this);
          this.parametersToState(this.props.parameters, this.state);
          this.callbackIndex = -1;
          this.shortcuts = {
            [SHORTCUTS.select]: this.selectVideos,
            [SHORTCUTS.group]: this.groupVideos,
            [SHORTCUTS.search]: this.searchVideos,
            [SHORTCUTS.sort]: this.sortVideos,
            [SHORTCUTS.reload]: this.reloadDatabase,
            [SHORTCUTS.manageProperties]: this.manageProperties
          };
        }

        render() {
          const nbVideos = this.state.nbVideos;
          const nbPages = this.state.nbPages;
          const validSize = this.state.validSize;
          const validLength = this.state.validLength;
          const notFound = this.state.notFound;
          const groupDef = this.state.groupDef;
          const stringSetProperties = this.getStringSetProperties(this.state.properties);
          const multipleProperties = this.getMultipleProperties(this.state.properties);
          return /*#__PURE__*/React.createElement("div", {
            id: "videos"
          }, /*#__PURE__*/React.createElement("header", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: "Options"
          }, /*#__PURE__*/React.createElement(Menu, {
            title: "Filter videos ..."
          }, /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.select,
            action: this.selectVideos
          }, "Select videos ..."), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.group,
            action: this.groupVideos
          }, "Group ..."), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.search,
            action: this.searchVideos
          }, "Search ..."), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.sort,
            action: this.sortVideos
          }, "Sort ...")), notFound || !nbVideos ? '' : /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openRandomVideo
          }, "Open random video"), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.reload,
            action: this.reloadDatabase
          }, "Reload database ..."), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.manageProperties,
            action: this.manageProperties
          }, "Manage properties ..."), multipleProperties.length ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.classify
          }, "Classify ...") : '', stringSetProperties.length ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.fillWithKeywords
          }, "Put keywords into a property ...") : '', /*#__PURE__*/React.createElement(Menu, {
            title: "Page size ..."
          }, PAGE_SIZES.map((count, index) => /*#__PURE__*/React.createElement(MenuItemCheck, {
            key: index,
            checked: this.state.pageSize === count,
            action: checked => {
              if (checked) this.setPageSize(count);
            }
          }, count, " video", count > 1 ? 's' : '', " per page"))), /*#__PURE__*/React.createElement(MenuItemCheck, {
            checked: this.state.confirmDeletion,
            action: this.confirmDeletionForNotFound
          }, "confirm deletion for entries not found")), /*#__PURE__*/React.createElement("div", {
            className: "buttons"
          }), /*#__PURE__*/React.createElement("div", {
            className: "pagination"
          }, /*#__PURE__*/React.createElement(Pagination, {
            singular: "page",
            plural: "pages",
            nbPages: nbPages,
            pageNumber: this.state.pageNumber,
            key: this.state.pageNumber,
            onChange: this.changePage
          }))), /*#__PURE__*/React.createElement("div", {
            className: "frontier"
          }), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, /*#__PURE__*/React.createElement("div", {
            className: "side-panel"
          }, /*#__PURE__*/React.createElement("div", {
            className: "stack filter"
          }, /*#__PURE__*/React.createElement("div", {
            className: "stack-title",
            onClick: this.stackFilter
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, "Filter"), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, this.state.stackFilter ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP)), this.state.stackFilter ? '' : /*#__PURE__*/React.createElement("div", {
            className: "stack-content"
          }, /*#__PURE__*/React.createElement(Filter, {
            page: this
          }))), groupDef ? /*#__PURE__*/React.createElement("div", {
            className: "stack group"
          }, /*#__PURE__*/React.createElement("div", {
            className: "stack-title",
            onClick: this.stackGroup
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, "Groups"), /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, this.state.stackGroup ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP)), this.state.stackGroup ? '' : /*#__PURE__*/React.createElement("div", {
            className: "stack-content"
          }, /*#__PURE__*/React.createElement(GroupView, {
            groupID: groupDef.group_id,
            field: groupDef.field,
            sorting: groupDef.sorting,
            reverse: groupDef.reverse,
            groups: groupDef.groups,
            onSelect: this.selectGroup,
            onOptions: this.editPropertyValue
          }))) : ''), /*#__PURE__*/React.createElement("div", {
            className: "main-panel videos"
          }, this.renderVideos())), /*#__PURE__*/React.createElement("footer", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "footer-status",
            onClick: this.resetStatus
          }, this.state.status), /*#__PURE__*/React.createElement("div", {
            className: "footer-information"
          }, groupDef ? /*#__PURE__*/React.createElement("div", {
            className: "info group"
          }, "Group ", groupDef.group_id + 1, "/", groupDef.nb_groups) : '', /*#__PURE__*/React.createElement("div", {
            className: "info count"
          }, nbVideos, " video", nbVideos > 1 ? 's' : ''), /*#__PURE__*/React.createElement("div", {
            className: "info size"
          }, validSize), /*#__PURE__*/React.createElement("div", {
            className: "info length"
          }, validLength))));
        }

        renderVideos() {
          return this.state.videos.map(data => /*#__PURE__*/React.createElement(Video, {
            key: data.video_id,
            data: data,
            index: data.local_id,
            parent: this,
            confirmDeletion: this.state.confirmDeletion
          }));
        }

        componentDidMount() {
          this.callbackIndex = KEYBOARD_MANAGER.register(this.checkShortcut);
        }

        parametersToState(parameters, state) {
          state.pageSize = parameters.pageSize;
          state.pageNumber = parameters.pageNumber;
          state.nbVideos = parameters.info.nbVideos;
          state.nbPages = parameters.info.nbPages;
          state.validSize = parameters.info.validSize;
          state.validLength = parameters.info.validLength;
          state.notFound = parameters.info.notFound;
          state.groupDef = parameters.info.groupDef;
          state.searchDef = parameters.info.searchDef;
          state.sources = parameters.info.sources;
          state.sorting = parameters.info.sorting;
          state.sourceTree = parameters.info.sourceTree;
          state.properties = parameters.info.properties;
          state.videos = parameters.info.videos;
        }

        scrollTop() {
          const videos = document.querySelector('#videos .videos');
          videos.scrollTop = 0;
        }

        updatePage(state, top = true) {
          // todo what if page size is out or page range ?
          const pageSize = state.pageSize !== undefined ? state.pageSize : this.state.pageSize;
          const pageNumber = state.pageNumber !== undefined ? state.pageNumber : this.state.pageNumber;
          python_call('get_info_and_videos', pageSize, pageNumber, FIELDS).then(info => {
            this.parametersToState({
              pageSize,
              pageNumber,
              info
            }, state);
            if (top) this.setState(state, this.scrollTop);else this.setState(state);
          }).catch(backend_error);
        }

        updateStatus(status, reload = false, top = false) {
          if (reload) {
            this.updatePage({
              status
            }, top);
          } else {
            this.setState({
              status
            });
          }
        }

        resetStatus() {
          this.updateStatus("Ready.");
        }

        componentWillUnmount() {
          KEYBOARD_MANAGER.unregister(this.callbackIndex);
        }
        /**
         * @param event {KeyboardEvent}
         */


        checkShortcut(event) {
          for (let shortcut of Object.values(SHORTCUTS)) {
            if (shortcutPressed(event, shortcut)) {
              setTimeout(() => this.shortcuts[shortcut](), 0);
              return true;
            }
          }
        }

        selectVideos() {
          this.props.app.loadDialog('Select Videos', onClose => /*#__PURE__*/React.createElement(FormSourceVideo, {
            tree: this.state.sourceTree,
            sources: this.state.sources,
            onClose: sources => {
              onClose();

              if (sources && sources.length) {
                python_call('set_sources', sources).then(() => this.updatePage({
                  pageNumber: 0
                })).catch(backend_error);
              }
            }
          }));
        }

        groupVideos() {
          const group_def = this.state.groupDef || {
            field: null,
            reverse: null
          };
          this.props.app.loadDialog('Group videos:', onClose => /*#__PURE__*/React.createElement(FormGroup, {
            definition: group_def,
            properties: this.state.properties,
            onClose: criterion => {
              onClose();

              if (criterion) {
                python_call('group_videos', criterion.field, criterion.sorting, criterion.reverse, criterion.allowSingletons, criterion.allowMultiple).then(() => this.updatePage({
                  pageNumber: 0
                })).catch(backend_error);
              }
            }
          }));
        }

        searchVideos() {
          const search_def = this.state.searchDef || {
            text: null,
            cond: null
          };
          this.props.app.loadDialog('Search videos', onClose => /*#__PURE__*/React.createElement(FormSearch, {
            text: search_def.text,
            cond: search_def.cond,
            onClose: criterion => {
              onClose();

              if (criterion && criterion.text.length && criterion.cond.length) {
                python_call('set_search', criterion.text, criterion.cond).then(() => this.updatePage({
                  pageNumber: 0
                })).catch(backend_error);
              }
            }
          }));
        }

        sortVideos() {
          const sorting = this.state.sorting;
          this.props.app.loadDialog('Sort videos', onClose => /*#__PURE__*/React.createElement(FormSort, {
            sorting: sorting,
            onClose: sorting => {
              onClose();

              if (sorting && sorting.length) {
                python_call('set_sorting', sorting).then(() => this.updatePage({
                  pageNumber: 0
                })).catch(backend_error);
              }
            }
          }));
        }

        resetGroup() {
          python_call('group_videos', '').then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        resetSearch() {
          python_call('set_search', null, null).then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        resetSort() {
          python_call('set_sorting', []).then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        openRandomVideo() {
          python_call('open_random_video').then(filename => {
            this.setState({
              status: `Randomly opened: ${filename}`
            });
          }).catch(backend_error);
        }

        reloadDatabase() {
          this.props.app.loadPage("home", {
            update: true
          });
        }

        manageProperties() {
          this.props.app.loadPropertiesPage();
        }

        classify() {
          this.props.app.loadDialog('Choose property to classify:', onClose => /*#__PURE__*/React.createElement(FormSetClassification, {
            properties: this.getMultipleProperties(this.state.properties),
            onClose: field => {
              onClose();

              if (field) {
                python_call('classifier_set_property', field).then(data => this.props.app.loadClassificationPage(data)).catch(backend_error);
              }
            }
          }));
        }

        fillWithKeywords() {
          this.props.app.loadDialog(`Fill property`, onClose => /*#__PURE__*/React.createElement(FormFillKeywords, {
            properties: this.getStringSetProperties(this.state.properties),
            onClose: state => {
              onClose();

              if (state) {
                python_call('fill_property_with_terms', state.field, state.onlyEmpty).then(() => this.updateStatus(`Filled property "${state.field}" with video keywords.`, true, true)).catch(backend_error);
              }
            }
          }));
        }

        setPageSize(count) {
          if (count !== this.state.pageSize) this.updatePage({
            pageSize: count,
            pageNumber: 0
          });
        }

        confirmDeletionForNotFound(checked) {
          this.setState({
            confirmDeletion: checked
          });
        }

        changeGroup(groupNumber) {
          python_call('set_group', groupNumber).then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        selectGroup(value) {
          if (value === -1) this.resetGroup();else this.changeGroup(value);
        }

        changePage(pageNumber) {
          this.updatePage({
            pageNumber
          });
        }

        stackGroup() {
          this.setState({
            stackGroup: !this.state.stackGroup
          });
        }

        stackFilter() {
          this.setState({
            stackFilter: !this.state.stackFilter
          });
        }

        getStringSetProperties(definitions) {
          const properties = [];

          for (let def of definitions) {
            if (def.multiple && def.type === "str") properties.push(def);
          }

          return properties;
        }

        getMultipleProperties(definitions) {
          const properties = [];

          for (let def of definitions) {
            if (def.multiple) properties.push(def);
          }

          return properties;
        }

        generatePropTable(definitions) {
          const properties = {};

          for (let def of definitions) {
            properties[def.name] = def;
          }

          return properties;
        }

        editPropertyValue(index) {
          const groupDef = this.state.groupDef;
          const name = groupDef.field.substr(1);
          const value = groupDef.groups[index].value;
          this.props.app.loadDialog(`Property "${name}", value "${value}"`, onClose => /*#__PURE__*/React.createElement(FormEditPropertyValue, {
            properties: this.generatePropTable(this.state.properties),
            name: name,
            value: value,
            onClose: operation => {
              onClose();

              if (operation) {
                switch (operation.form) {
                  case 'delete':
                    python_call('delete_property_value', name, value).then(() => this.updateStatus(`Property value deleted: "${name}" / "${value}"`, true)).catch(backend_error);
                    break;

                  case 'edit':
                    python_call('edit_property_value', name, value, operation.value).then(() => this.updateStatus(`Property value edited: "${name}" : "${value}" -> "${operation.value}"`, true)).catch(backend_error);
                    break;

                  case 'move':
                    python_call('move_property_value', name, value, operation.move).then(() => this.updateStatus(`Property value moved: "${value}" from "${name}" to "${operation.move}"`, true)).catch(backend_error);
                    break;
                }
              }
            }
          }));
        }

      });
    }
  };
});