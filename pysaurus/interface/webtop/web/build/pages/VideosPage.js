System.register(["../utils/constants.js", "../components/MenuPack.js", "../components/Pagination.js", "../pageComponents/Video.js", "../forms/FormSourceVideo.js", "../forms/FormGroup.js", "../forms/FormSearch.js", "../forms/FormSort.js", "../pageComponents/GroupView.js", "../forms/FormEditPropertyValue.js", "../forms/FormFillKeywords.js", "../forms/FormPropertyMultiVideo.js", "../components/Collapsable.js", "../components/Cross.js", "../components/SettingIcon.js", "../components/MenuItem.js", "../components/MenuItemCheck.js", "../components/MenuItemRadio.js", "../components/Menu.js"], function (_export, _context) {
  "use strict";

  var PAGE_SIZES, SEARCH_TYPE_TITLE, SOURCE_TREE, MenuPack, Pagination, Video, FormSourceVideo, FormGroup, FormSearch, FormSort, GroupView, FormEditPropertyValue, FormFillKeywords, FormPropertyMultiVideo, Collapsable, Cross, SettingIcon, MenuItem, MenuItemCheck, MenuItemRadio, Menu, Shortcut, Action, Actions, Filter, VideosPage;

  _export("VideosPage", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      PAGE_SIZES = _utilsConstantsJs.PAGE_SIZES;
      SEARCH_TYPE_TITLE = _utilsConstantsJs.SEARCH_TYPE_TITLE;
      SOURCE_TREE = _utilsConstantsJs.SOURCE_TREE;
    }, function (_componentsMenuPackJs) {
      MenuPack = _componentsMenuPackJs.MenuPack;
    }, function (_componentsPaginationJs) {
      Pagination = _componentsPaginationJs.Pagination;
    }, function (_pageComponentsVideoJs) {
      Video = _pageComponentsVideoJs.Video;
    }, function (_formsFormSourceVideoJs) {
      FormSourceVideo = _formsFormSourceVideoJs.FormSourceVideo;
    }, function (_formsFormGroupJs) {
      FormGroup = _formsFormGroupJs.FormGroup;
    }, function (_formsFormSearchJs) {
      FormSearch = _formsFormSearchJs.FormSearch;
    }, function (_formsFormSortJs) {
      FormSort = _formsFormSortJs.FormSort;
    }, function (_pageComponentsGroupViewJs) {
      GroupView = _pageComponentsGroupViewJs.GroupView;
    }, function (_formsFormEditPropertyValueJs) {
      FormEditPropertyValue = _formsFormEditPropertyValueJs.FormEditPropertyValue;
    }, function (_formsFormFillKeywordsJs) {
      FormFillKeywords = _formsFormFillKeywordsJs.FormFillKeywords;
    }, function (_formsFormPropertyMultiVideoJs) {
      FormPropertyMultiVideo = _formsFormPropertyMultiVideoJs.FormPropertyMultiVideo;
    }, function (_componentsCollapsableJs) {
      Collapsable = _componentsCollapsableJs.Collapsable;
    }, function (_componentsCrossJs) {
      Cross = _componentsCrossJs.Cross;
    }, function (_componentsSettingIconJs) {
      SettingIcon = _componentsSettingIconJs.SettingIcon;
    }, function (_componentsMenuItemJs) {
      MenuItem = _componentsMenuItemJs.MenuItem;
    }, function (_componentsMenuItemCheckJs) {
      MenuItemCheck = _componentsMenuItemCheckJs.MenuItemCheck;
    }, function (_componentsMenuItemRadioJs) {
      MenuItemRadio = _componentsMenuItemRadioJs.MenuItemRadio;
    }, function (_componentsMenuJs) {
      Menu = _componentsMenuJs.Menu;
    }],
    execute: function () {
      Shortcut = class Shortcut {
        /**
         * Initialize.
         * @param shortcut {string}
         */
        constructor(shortcut) {
          const pieces = shortcut.split("+").map(piece => piece.toLowerCase());
          const specialKeys = new Set(pieces.slice(0, pieces.length - 1));
          this.str = shortcut;
          this.ctrl = specialKeys.has("ctrl");
          this.alt = specialKeys.has("alt");
          this.shift = specialKeys.has("shift") || specialKeys.has("maj");
          this.key = pieces[pieces.length - 1];
        }
        /**
         * Returns true if event corresponds to shortcut.
         * @param event {KeyboardEvent}
         */


        isPressed(event) {
          return this.key === event.key.toLowerCase() && this.ctrl === event.ctrlKey && this.alt === event.altKey && this.shift === event.shiftKey;
        }

      };
      Action = class Action {
        /**
         * Initialize.
         * @param shortcut {string}
         * @param title {string}
         * @param callback {function}
         */
        constructor(shortcut, title, callback) {
          this.shortcut = new Shortcut(shortcut);
          this.title = title;
          this.callback = callback;
        }

        toMenuItem(title = undefined) {
          return /*#__PURE__*/React.createElement(MenuItem, {
            shortcut: this.shortcut.str,
            action: this.callback
          }, title || this.title);
        }

        toSettingIcon(title = undefined) {
          return /*#__PURE__*/React.createElement(SettingIcon, {
            title: `${title || this.title} (${this.shortcut.str})`,
            action: this.callback
          });
        }

        toCross(title = undefined) {
          return /*#__PURE__*/React.createElement(Cross, {
            title: `${title || this.title} (${this.shortcut.str})`,
            action: this.callback
          });
        }

      };
      Actions = class Actions {
        /**
         * @param actions {Object.<string, Action>}
         */
        constructor(actions) {
          /** @type {Object.<string, Action>} */
          this.actions = actions;
          const shortcutToName = {};

          for (let name of Object.keys(actions)) {
            const shortcut = actions[name].shortcut.str;
            if (shortcutToName.hasOwnProperty(shortcut)) throw new Error(`Duplicated shortcut ${shortcut} for ${shortcutToName[shortcut]} and ${name}`);
            shortcutToName[shortcut] = name;
          }

          this.onKeyPressed = this.onKeyPressed.bind(this);
        }
        /**
         * Callback to trigger shortcuts on keyboard events.
         * @param event {KeyboardEvent}
         * @returns {boolean}
         */


        onKeyPressed(event) {
          for (let action of Object.values(this.actions)) {
            if (action.shortcut.isPressed(event)) {
              setTimeout(() => action.callback(), 0);
              return true;
            }
          }
        }

      };
      Filter = class Filter extends React.Component {
        constructor(props) {
          // page: VideosPage
          super(props);
        }

        static compareSources(sources1, sources2) {
          if (sources1.length !== sources2.length) return false;

          for (let i = 0; i < sources1.length; ++i) {
            const path1 = sources1[i];
            const path2 = sources2[i];
            if (path1.length !== path2.length) return false;

            for (let j = 0; j < path1.length; ++j) {
              if (path1[j] !== path2[j]) return false;
            }
          }

          return true;
        }

        render() {
          const app = this.props.page;
          const backend = app.state;
          const sources = backend.sources;
          const groupDef = backend.groupDef;
          const searchDef = backend.searchDef;
          const sorting = backend.sorting;
          const sortingIsDefault = sorting.length === 1 && sorting[0] === '-date';
          const selectionSize = backend.selection.size;
          const selectedAll = backend.realNbVideos === selectionSize;
          const features = app.features;
          return /*#__PURE__*/React.createElement("table", {
            className: "filter"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, sources.map((source, index) => /*#__PURE__*/React.createElement("div", {
            key: index
          }, source.join(' ').replace('_', ' ')))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, features.actions.select.toSettingIcon()), !Filter.compareSources(window.PYTHON_DEFAULT_SOURCES, sources) ? /*#__PURE__*/React.createElement("div", null, features.actions.unselect.toCross()) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, groupDef ? /*#__PURE__*/React.createElement("div", null, "Grouped") : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, "Ungrouped")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, features.actions.group.toSettingIcon(groupDef ? 'Edit ...' : 'Group ...')), groupDef ? /*#__PURE__*/React.createElement("div", null, features.actions.ungroup.toCross()) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, "Searched ", SEARCH_TYPE_TITLE[searchDef.cond]), /*#__PURE__*/React.createElement("div", null, "\"", /*#__PURE__*/React.createElement("strong", null, searchDef.text), "\"")) : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, "No search")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, features.actions.search.toSettingIcon(searchDef ? 'Edit ...' : 'Search ...')), searchDef ? /*#__PURE__*/React.createElement("div", null, features.actions.unsearch.toCross()) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, "Sorted by"), sorting.map((val, i) => /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, val.substr(1)), ' ', val[0] === '-' ? /*#__PURE__*/React.createElement("span", null, "\u25BC") : /*#__PURE__*/React.createElement("span", null, "\u25B2")))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, features.actions.sort.toSettingIcon()), sortingIsDefault ? '' : /*#__PURE__*/React.createElement("div", null, features.actions.unsort.toCross()))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, selectionSize ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, "Selected"), /*#__PURE__*/React.createElement("div", null, selectedAll ? 'all' : '', " ", selectionSize, " ", selectedAll ? '' : `/ ${backend.nbVideos}`, " video", selectionSize < 2 ? '' : 's'), /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: app.displayOnlySelected
          }, backend.displayOnlySelected ? 'Display all videos' : 'Display only selected videos'))) : /*#__PURE__*/React.createElement("div", null, "No videos selected"), selectedAll ? '' : /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: app.selectAll
          }, "select all")), selectionSize ? /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: "Edit property ..."
          }, backend.properties.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => app.editPropertiesForManyVideos(def.name)
          }, def.name)))) : ''), /*#__PURE__*/React.createElement("td", null, selectionSize ? /*#__PURE__*/React.createElement(Cross, {
            title: `Deselect all`,
            action: app.deselect
          }) : ''))));
        }

      };

      _export("VideosPage", VideosPage = class VideosPage extends React.Component {
        constructor(props) {
          // parameters: {backend state}
          // app: App
          super(props);
          this.state = Object.assign({
            status: 'Loaded.',
            confirmDeletion: true,
            path: [],
            selection: new Set(),
            displayOnlySelected: false
          }, this.props.parameters);
          this.backendGroupVideos = this.backendGroupVideos.bind(this);
          this.changeGroup = this.changeGroup.bind(this);
          this.changePage = this.changePage.bind(this);
          this.classifierConcatenate = this.classifierConcatenate.bind(this);
          this.classifierSelectGroup = this.classifierSelectGroup.bind(this);
          this.classifierUnstack = this.classifierUnstack.bind(this);
          this.confirmDeletionForNotFound = this.confirmDeletionForNotFound.bind(this);
          this.deselect = this.deselect.bind(this);
          this.displayOnlySelected = this.displayOnlySelected.bind(this);
          this.editPropertiesForManyVideos = this.editPropertiesForManyVideos.bind(this);
          this.editPropertyValue = this.editPropertyValue.bind(this);
          this.fillWithKeywords = this.fillWithKeywords.bind(this);
          this.focusPropertyValue = this.focusPropertyValue.bind(this);
          this.groupVideos = this.groupVideos.bind(this);
          this.manageProperties = this.manageProperties.bind(this);
          this.onVideoSelection = this.onVideoSelection.bind(this);
          this.openRandomVideo = this.openRandomVideo.bind(this);
          this.reloadDatabase = this.reloadDatabase.bind(this);
          this.resetGroup = this.resetGroup.bind(this);
          this.resetSearch = this.resetSearch.bind(this);
          this.resetSort = this.resetSort.bind(this);
          this.resetStatus = this.resetStatus.bind(this);
          this.reverseClassifierPath = this.reverseClassifierPath.bind(this);
          this.scrollTop = this.scrollTop.bind(this);
          this.searchVideos = this.searchVideos.bind(this);
          this.selectAll = this.selectAll.bind(this);
          this.selectGroup = this.selectGroup.bind(this);
          this.selectVideos = this.selectVideos.bind(this);
          this.setPageSize = this.setPageSize.bind(this);
          this.sortVideos = this.sortVideos.bind(this);
          this.unselectVideos = this.unselectVideos.bind(this);
          this.updatePage = this.updatePage.bind(this);
          this.updateStatus = this.updateStatus.bind(this);
          this.callbackIndex = -1;
          this.features = new Actions({
            select: new Action("Ctrl+T", "Select videos ...", this.selectVideos),
            group: new Action("Ctrl+G", "Group ...", this.groupVideos),
            search: new Action("Ctrl+F", "Search ...", this.searchVideos),
            sort: new Action("Ctrl+S", "Sort ...", this.sortVideos),
            unselect: new Action("Ctrl+Shift+T", "Reset selection", this.unselectVideos),
            ungroup: new Action("Ctrl+Shift+G", "Reset group", this.resetGroup),
            unsearch: new Action("Ctrl+Shift+F", "Reset search", this.resetSearch),
            unsort: new Action("Ctrl+Shift+S", "Reset sorting", this.resetSort),
            reload: new Action("Ctrl+R", "Reload database ...", this.reloadDatabase),
            manageProperties: new Action("Ctrl+P", "Manage properties ...", this.manageProperties),
            openRandomVideo: new Action("Ctrl+O", "Open random video", this.openRandomVideo)
          });
        }

        render() {
          const nbVideos = this.state.nbVideos;
          const nbPages = this.state.nbPages;
          const validSize = this.state.validSize;
          const validLength = this.state.validLength;
          const notFound = this.state.notFound;
          const groupDef = this.state.groupDef;
          const stringSetProperties = this.getStringSetProperties(this.state.properties);
          const stringProperties = this.getStringProperties(this.state.properties);
          const groupField = groupDef && groupDef.field.charAt(0) === ':' ? groupDef.field.substr(1) : null;
          return /*#__PURE__*/React.createElement("div", {
            id: "videos"
          }, /*#__PURE__*/React.createElement("header", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: "Options"
          }, /*#__PURE__*/React.createElement(Menu, {
            title: "Filter videos ..."
          }, this.features.actions.select.toMenuItem(), this.features.actions.group.toMenuItem(), this.features.actions.search.toMenuItem(), this.features.actions.sort.toMenuItem()), notFound || !nbVideos ? '' : this.features.actions.openRandomVideo.toMenuItem(), this.features.actions.reload.toMenuItem(), this.features.actions.manageProperties.toMenuItem(), stringSetProperties.length ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.fillWithKeywords
          }, "Put keywords into a property ...") : '', /*#__PURE__*/React.createElement(Menu, {
            title: "Page size ..."
          }, PAGE_SIZES.map((count, index) => /*#__PURE__*/React.createElement(MenuItemRadio, {
            key: index,
            checked: this.state.pageSize === count,
            value: count,
            action: this.setPageSize
          }, count, " video", count > 1 ? 's' : '', " per page"))), /*#__PURE__*/React.createElement(MenuItemCheck, {
            checked: this.state.confirmDeletion,
            action: this.confirmDeletionForNotFound
          }, "confirm deletion for entries not found"), this.state.properties.length > 10 ? /*#__PURE__*/React.createElement(Menu, {
            title: "Group videos by property ..."
          }, this.state.properties.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.backendGroupVideos(`:${def.name}`)
          }, def.name))) : this.state.properties.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.backendGroupVideos(`:${def.name}`)
          }, "Group videos by property: ", def.name))), /*#__PURE__*/React.createElement("div", {
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
          }, /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "filter",
            title: "Filter"
          }, /*#__PURE__*/React.createElement(Filter, {
            page: this
          })), this.state.path.length ? /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "filter",
            title: "Classifier path"
          }, stringProperties.length ? /*#__PURE__*/React.createElement("div", {
            className: "path-menu"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: "Concatenate path into ..."
          }, stringProperties.map((def, i) => /*#__PURE__*/React.createElement(MenuItem, {
            key: i,
            action: () => this.classifierConcatenate(def.name)
          }, def.name)), /*#__PURE__*/React.createElement(MenuItem, {
            action: () => this.classifierConcatenate(groupField)
          }, groupField)), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("button", {
            onClick: this.reverseClassifierPath
          }, "reverse path"))) : '', this.state.path.map((value, index) => /*#__PURE__*/React.createElement("div", {
            key: index,
            className: "path-step horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "title"
          }, value.toString()), index === this.state.path.length - 1 ? /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, /*#__PURE__*/React.createElement(Cross, {
            title: "unstack",
            action: this.classifierUnstack
          })) : ''))) : '', groupDef ? /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "group",
            title: "Groups"
          }, /*#__PURE__*/React.createElement(GroupView, {
            key: `${groupDef.field}-${groupDef.groups.length}-${this.state.path.join('-')}`,
            groupID: groupDef.group_id,
            field: groupDef.field,
            sorting: groupDef.sorting,
            reverse: groupDef.reverse,
            groups: groupDef.groups,
            inPath: this.state.path.length,
            onSelect: this.selectGroup,
            onOptions: this.editPropertyValue,
            onPlus: groupDef.field[0] === ':' && this.state.definitions[groupDef.field.substr(1)].multiple ? this.classifierSelectGroup : null
          })) : ''), /*#__PURE__*/React.createElement("div", {
            className: "main-panel videos"
          }, this.state.videos.map(data => /*#__PURE__*/React.createElement(Video, {
            key: data.video_id,
            data: data,
            parent: this,
            selected: this.state.selection.has(data.video_id),
            onSelect: this.onVideoSelection,
            confirmDeletion: this.state.confirmDeletion
          })))), /*#__PURE__*/React.createElement("footer", {
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

        componentDidMount() {
          this.callbackIndex = KEYBOARD_MANAGER.register(this.features.onKeyPressed);
        }

        componentWillUnmount() {
          KEYBOARD_MANAGER.unregister(this.callbackIndex);
        }

        scrollTop() {
          const videos = document.querySelector('#videos .videos');
          videos.scrollTop = 0;
        }

        updatePage(state, top = true) {
          const pageSize = state.pageSize !== undefined ? state.pageSize : this.state.pageSize;
          const pageNumber = state.pageNumber !== undefined ? state.pageNumber : this.state.pageNumber;
          const displayOnlySelected = state.displayOnlySelected !== undefined ? state.displayOnlySelected : this.state.displayOnlySelected;
          const selection = displayOnlySelected ? Array.from(state.selection !== undefined ? state.selection : this.state.selection) : [];
          python_call('get_info_and_videos', pageSize, pageNumber, selection).then(info => {
            this.setState(Object.assign(state, info), top ? this.scrollTop : undefined);
          }).catch(backend_error);
        }

        onVideoSelection(videoID, selected) {
          const selection = new Set(this.state.selection);

          if (selected) {
            selection.add(videoID);
            this.setState({
              selection
            });
          } else if (selection.has(videoID)) {
            selection.delete(videoID);
            const displayOnlySelected = this.state.displayOnlySelected && selection.size;
            const state = {
              selection,
              displayOnlySelected
            };
            if (this.state.displayOnlySelected) this.updatePage(state);else this.setState(state);
          }
        }

        deselect() {
          this.setState({
            selection: new Set(),
            displayOnlySelected: false
          });
        }

        selectAll() {
          python_call('get_view_indices').then(indices => this.setState({
            selection: new Set(indices)
          })).catch(backend_error);
        }

        displayOnlySelected() {
          this.updatePage({
            displayOnlySelected: !this.state.displayOnlySelected
          });
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

        unselectVideos() {
          python_call('set_sources', null).then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        selectVideos() {
          this.props.app.loadDialog('Select Videos', onClose => /*#__PURE__*/React.createElement(FormSourceVideo, {
            tree: SOURCE_TREE,
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
                python_call('set_groups', criterion.field, criterion.sorting, criterion.reverse, criterion.allowSingletons, criterion.allowMultiple).then(() => this.updatePage({
                  pageNumber: 0
                })).catch(backend_error);
              }
            }
          }));
        }

        backendGroupVideos(field, sorting = "count", reverse = true, allowSingletons = true, allowMultiple = true) {
          python_call('set_groups', field, sorting, reverse, allowSingletons, allowMultiple).then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        editPropertiesForManyVideos(propertyName) {
          const videos = Array.from(this.state.selection);
          python_call('count_prop_values', propertyName, videos).then(valuesAndCounts => this.props.app.loadDialog(`Edit property "${propertyName}" for ${this.state.selection.size} video${this.state.selection.size < 2 ? '' : 's'}`, onClose => /*#__PURE__*/React.createElement(FormPropertyMultiVideo, {
            nbVideos: this.state.selection.size,
            definition: this.state.definitions[propertyName],
            values: valuesAndCounts,
            onClose: edition => {
              onClose();

              if (edition) {
                python_call('edit_property_for_videos', propertyName, videos, edition.add, edition.remove).then(() => this.updateStatus(`Edited property "${propertyName}" for ${this.state.selection.size} video${this.state.selection.size < 2 ? '' : 's'}`, true)).catch(backend_error);
              }
            }
          }))).catch(backend_error);
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
          python_call('set_groups', '').then(() => this.updatePage({
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
          if (this.state.notFound || !this.state.nbVideos) return;
          python_call('open_random_video').then(filename => {
            this.setState({
              status: `Randomly opened: ${filename}`
            });
          }).catch(backend_error);
        }

        reloadDatabase() {
          this.props.app.loadHomePage(true);
        }

        manageProperties() {
          this.props.app.loadPropertiesPage();
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

        getStringSetProperties(definitions) {
          const properties = [];

          for (let def of definitions) {
            if (def.multiple && def.type === "str") properties.push(def);
          }

          return properties;
        }

        getStringProperties(definitions) {
          const field = this.state.groupDef ? this.state.groupDef.field : null;
          const properties = [];

          for (let def of definitions) {
            if (def.type === "str" && (!field || field.charAt(0) !== ':' || def.name !== field.substr(1))) properties.push(def);
          }

          return properties;
        }

        reverseClassifierPath() {
          python_call('classifier_reverse').then(path => this.setState({
            path
          })).catch(backend_error);
        }
        /**
         *
         * @param indicesSet {Set}
         */


        editPropertyValue(indicesSet) {
          const groupDef = this.state.groupDef;
          const name = groupDef.field.substr(1);
          const values = [];
          const indices = [];

          for (let index of indicesSet.values()) indices.push(index);

          indices.sort();

          for (let index of indices) values.push(groupDef.groups[index].value);

          let title;
          if (values.length === 1) title = `Property "${name}", value "${values[0]}"`;else title = `Property "${name}", ${values.length} values"`;
          this.props.app.loadDialog(title, onClose => /*#__PURE__*/React.createElement(FormEditPropertyValue, {
            properties: this.state.definitions,
            name: name,
            values: values,
            onClose: operation => {
              onClose();

              if (operation) {
                switch (operation.form) {
                  case 'delete':
                    python_call('delete_property_value', name, values).then(() => this.updateStatus(`Property value deleted: "${name}" / "${values.join('", "')}"`, true)).catch(backend_error);
                    break;

                  case 'edit':
                    python_call('edit_property_value', name, values, operation.value).then(() => this.updateStatus(`Property value edited: "${name}" : "${values.join('", "')}" -> "${operation.value}"`, true)).catch(backend_error);
                    break;

                  case 'move':
                    python_call('move_property_value', name, values, operation.move).then(() => this.updateStatus(`Property value moved: "${values.join('", "')}" from "${name}" to "${operation.move}"`, true)).catch(backend_error);
                    break;
                }
              }
            }
          }));
        }

        classifierSelectGroup(index) {
          python_call('classifier_select_group', index).then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        classifierUnstack() {
          python_call('classifier_back').then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        classifierConcatenate(outputPropertyName) {
          python_call('classifier_concatenate_path', outputPropertyName).then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

        focusPropertyValue(propertyName, propertyValue) {
          python_call('set_groups', `:${propertyName}`, "count", true, true, true).then(() => python_call('classifier_select_group_by_value', propertyValue)).then(() => this.updatePage({
            pageNumber: 0
          })).catch(backend_error);
        }

      });
    }
  };
});