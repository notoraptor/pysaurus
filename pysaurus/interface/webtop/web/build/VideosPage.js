System.register(["./buttons.js", "./constants.js", "./MenuPack.js", "./Pagination.js", "./Video.js", "./FormSourceVideo.js", "./FormGroup.js", "./FormSearch.js", "./FormSort.js"], function (_export, _context) {
  "use strict";

  var SettingIcon, Cross, FIELD_TITLES, PAGE_SIZES, FIELDS, SEARCH_TYPE_TITLE, MenuPack, MenuItem, Menu, MenuItemCheck, Pagination, Video, FormSourceVideo, FormGroup, FormSearch, FormSort, Filter, VideosPage, SHORTCUTS, SPECIAL_KEYS;

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
      FIELD_TITLES = _constantsJs.FIELD_TITLES;
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
          const backend = this.props.page.state.info;
          const sources = backend.sources;
          const groupDef = backend.groupDef;
          const groupFieldValue = backend.groupFieldValue;
          const searchDef = backend.searchDef;
          const sorting = backend.sorting;
          const sortingIsDefault = sorting.length === 1 && sorting[0] === '-date';
          return /*#__PURE__*/React.createElement("table", {
            className: "filter"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "left"
          }, sources.map((source, index) => /*#__PURE__*/React.createElement("div", {
            className: "source",
            key: index
          }, source.join(' ').replace('_', ' ')))), /*#__PURE__*/React.createElement("td", {
            className: "right"
          }, /*#__PURE__*/React.createElement(SettingIcon, {
            title: `Select sources ... (${SHORTCUTS.select})`,
            action: app.selectVideos
          }))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "left"
          }, groupDef ? /*#__PURE__*/React.createElement("div", {
            className: "filter"
          }, /*#__PURE__*/React.createElement("div", null, "Grouped by"), /*#__PURE__*/React.createElement("div", null, FIELD_TITLES[groupDef.field], ' ', groupDef.reverse ? /*#__PURE__*/React.createElement("span", null, "\u25BC") : /*#__PURE__*/React.createElement("span", null, "\u25B2")), groupDef.nb_groups ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, "Group ", groupDef.group_id + 1, " / ", groupDef.nb_groups), /*#__PURE__*/React.createElement("div", null, Utils.sentence(FIELD_TITLES[groupDef.field]), ":", ' ', /*#__PURE__*/React.createElement("strong", null, groupFieldValue))) : '') : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, "Ungrouped")), /*#__PURE__*/React.createElement("td", {
            className: "right"
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SettingIcon, {
            title: (groupDef ? 'Edit ...' : 'Group ...') + ` (${SHORTCUTS.group})`,
            action: app.groupVideos
          })), groupDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Cross, {
            title: "Reset group",
            action: app.resetGroup
          })) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "left"
          }, searchDef ? /*#__PURE__*/React.createElement("div", {
            className: "filter"
          }, /*#__PURE__*/React.createElement("div", null, "Searched ", SEARCH_TYPE_TITLE[searchDef.cond]), /*#__PURE__*/React.createElement("div", null, "\"", /*#__PURE__*/React.createElement("strong", null, searchDef.text), "\"")) : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, "No search")), /*#__PURE__*/React.createElement("td", {
            className: "right"
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SettingIcon, {
            title: (searchDef ? 'Edit ...' : 'Search ...') + ` (${SHORTCUTS.search})`,
            action: app.searchVideos
          })), searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Cross, {
            title: "reset search",
            action: app.resetSearch
          })) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "left"
          }, /*#__PURE__*/React.createElement("div", null, "Sorted by"), sorting.map((val, i) => /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, val.substr(1)), ' ', val[0] === '-' ? /*#__PURE__*/React.createElement("span", null, "\u25BC") : /*#__PURE__*/React.createElement("span", null, "\u25B2")))), /*#__PURE__*/React.createElement("td", {
            className: "right"
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(SettingIcon, {
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
          const args = this.props.parameters;
          this.state = {
            pageSize: args.pageSize,
            pageNumber: args.pageNumber,
            status: 'Loaded.',
            confirmDeletion: true,
            info: args.info
          };
          this.callbackIndex = -1;
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
          const backend = this.state.info;
          const nbVideos = backend.nbVideos;
          const nbPages = backend.nbPages;
          const validSize = backend.validSize;
          const validLength = backend.validLength;
          const notFound = backend.notFound;
          const group_def = backend.groupDef;
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
            action: this.selectVideos
          }, "Group ..."), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.search,
            action: this.selectVideos
          }, "Search ..."), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.sort,
            action: this.selectVideos
          }, "Sort ...")), notFound || !nbVideos ? '' : /*#__PURE__*/React.createElement(MenuItem, {
            action: this.openRandomVideo
          }, "Open random video"), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.reload,
            action: this.reloadDatabase
          }, "Reload database ..."), /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: SHORTCUTS.manageProperties,
            action: this.manageProperties
          }, "Manage properties"), /*#__PURE__*/React.createElement(Menu, {
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
          }, group_def ? /*#__PURE__*/React.createElement(Pagination, {
            singular: "group",
            plural: "groups",
            nbPages: group_def.nb_groups,
            pageNumber: group_def.group_id,
            onChange: this.changeGroup
          }) : '', /*#__PURE__*/React.createElement(Pagination, {
            singular: "page",
            plural: "pages",
            nbPages: nbPages,
            pageNumber: this.state.pageNumber,
            onChange: this.changePage
          }))), /*#__PURE__*/React.createElement("div", {
            className: "frontier"
          }), /*#__PURE__*/React.createElement("div", {
            className: "content"
          }, /*#__PURE__*/React.createElement("div", {
            className: "wrapper"
          }, /*#__PURE__*/React.createElement("div", {
            className: "side-panel"
          }, /*#__PURE__*/React.createElement(Filter, {
            page: this
          })), /*#__PURE__*/React.createElement("div", {
            className: "main-panel videos"
          }, this.renderVideos()))), /*#__PURE__*/React.createElement("footer", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "footer-status",
            onClick: this.resetStatus
          }, this.state.status), /*#__PURE__*/React.createElement("div", {
            className: "footer-information"
          }, /*#__PURE__*/React.createElement("div", {
            className: "info count"
          }, nbVideos, " video", nbVideos > 1 ? 's' : ''), /*#__PURE__*/React.createElement("div", {
            className: "info size"
          }, validSize), /*#__PURE__*/React.createElement("div", {
            className: "info length"
          }, validLength))));
        }

        renderVideos() {
          return this.state.info.videos.map(data => /*#__PURE__*/React.createElement(Video, {
            key: data.video_id,
            data: data,
            index: data.local_id,
            parent: this,
            confirmDeletion: this.state.confirmDeletion
          }));
        }

        scrollTop() {
          const videos = document.querySelector('#videos .videos');
          videos.scrollTop = 0;
        }

        updatePage(state, top = true) {
          const pageSize = state.pageSize !== undefined ? state.pageSize : this.state.pageSize;
          const pageNumber = state.pageNumber !== undefined ? state.pageNumber : this.state.pageNumber;
          python_call('get_info_and_videos', pageSize, pageNumber, FIELDS).then(info => {
            state.pageSize = pageSize;
            state.pageNumber = pageNumber;
            state.info = info;
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

        componentDidMount() {
          this.callbackIndex = KEYBOARD_MANAGER.register(this.checkShortcut);
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
            tree: this.state.info.sourceTree,
            sources: this.state.info.sources,
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
          const group_def = this.state.info.groupDef || {
            field: null,
            reverse: null
          };
          this.props.app.loadDialog('Group videos with same:', onClose => /*#__PURE__*/React.createElement(FormGroup, {
            field: group_def.field,
            reverse: group_def.reverse,
            onClose: criterion => {
              onClose();

              if (criterion) {
                python_call('group_videos', criterion.field, criterion.reverse).then(() => this.updatePage({
                  pageNumber: 0
                })).catch(backend_error);
              }
            }
          }));
        }

        searchVideos() {
          const search_def = this.state.info.searchDef || {
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
          const sorting = this.state.info.sorting;
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
          python_call('group_videos', null, null).then(() => this.updatePage({
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

        changePage(pageNumber) {
          this.updatePage({
            pageNumber
          });
        }

      });
    }
  };
});