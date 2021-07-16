System.register(["../utils/constants.js", "../components/MenuPack.js", "../components/Pagination.js", "../components/Video.js", "../forms/FormVideosSource.js", "../forms/FormVideosGrouping.js", "../forms/FormVideosSearch.js", "../forms/FormVideosSort.js", "../components/GroupView.js", "../forms/FormPropertySelectedValues.js", "../forms/FormVideosKeywordsToProperty.js", "../forms/FormSelectedVideosProperty.js", "../components/Collapsable.js", "../components/Cross.js", "../components/MenuItem.js", "../components/MenuItemCheck.js", "../components/MenuItemRadio.js", "../components/Menu.js", "../utils/Selector.js", "../utils/Action.js", "../utils/Actions.js", "../components/ActionToMenuItem.js", "../components/ActionToSettingIcon.js", "../components/ActionToCross.js", "../utils/backend.js"], function (_export, _context) {
  "use strict";

  var PAGE_SIZES, SEARCH_TYPE_TITLE, SOURCE_TREE, MenuPack, Pagination, Video, FormVideosSource, FormVideosGrouping, FormVideosSearch, FormVideosSort, GroupView, FormPropertySelectedValues, FormVideosKeywordsToProperty, FormSelectedVideosProperty, Collapsable, Cross, MenuItem, MenuItemCheck, MenuItemRadio, Menu, Selector, Action, Actions, ActionToMenuItem, ActionToSettingIcon, ActionToCross, backend_error, python_call, VideosPage;

  function compareSources(sources1, sources2) {
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
    }, function (_componentsVideoJs) {
      Video = _componentsVideoJs.Video;
    }, function (_formsFormVideosSourceJs) {
      FormVideosSource = _formsFormVideosSourceJs.FormVideosSource;
    }, function (_formsFormVideosGroupingJs) {
      FormVideosGrouping = _formsFormVideosGroupingJs.FormVideosGrouping;
    }, function (_formsFormVideosSearchJs) {
      FormVideosSearch = _formsFormVideosSearchJs.FormVideosSearch;
    }, function (_formsFormVideosSortJs) {
      FormVideosSort = _formsFormVideosSortJs.FormVideosSort;
    }, function (_componentsGroupViewJs) {
      GroupView = _componentsGroupViewJs.GroupView;
    }, function (_formsFormPropertySelectedValuesJs) {
      FormPropertySelectedValues = _formsFormPropertySelectedValuesJs.FormPropertySelectedValues;
    }, function (_formsFormVideosKeywordsToPropertyJs) {
      FormVideosKeywordsToProperty = _formsFormVideosKeywordsToPropertyJs.FormVideosKeywordsToProperty;
    }, function (_formsFormSelectedVideosPropertyJs) {
      FormSelectedVideosProperty = _formsFormSelectedVideosPropertyJs.FormSelectedVideosProperty;
    }, function (_componentsCollapsableJs) {
      Collapsable = _componentsCollapsableJs.Collapsable;
    }, function (_componentsCrossJs) {
      Cross = _componentsCrossJs.Cross;
    }, function (_componentsMenuItemJs) {
      MenuItem = _componentsMenuItemJs.MenuItem;
    }, function (_componentsMenuItemCheckJs) {
      MenuItemCheck = _componentsMenuItemCheckJs.MenuItemCheck;
    }, function (_componentsMenuItemRadioJs) {
      MenuItemRadio = _componentsMenuItemRadioJs.MenuItemRadio;
    }, function (_componentsMenuJs) {
      Menu = _componentsMenuJs.Menu;
    }, function (_utilsSelectorJs) {
      Selector = _utilsSelectorJs.Selector;
    }, function (_utilsActionJs) {
      Action = _utilsActionJs.Action;
    }, function (_utilsActionsJs) {
      Actions = _utilsActionsJs.Actions;
    }, function (_componentsActionToMenuItemJs) {
      ActionToMenuItem = _componentsActionToMenuItemJs.ActionToMenuItem;
    }, function (_componentsActionToSettingIconJs) {
      ActionToSettingIcon = _componentsActionToSettingIconJs.ActionToSettingIcon;
    }, function (_componentsActionToCrossJs) {
      ActionToCross = _componentsActionToCrossJs.ActionToCross;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }],
    execute: function () {
      _export("VideosPage", VideosPage = class VideosPage extends React.Component {
        constructor(props) {
          // parameters: {backend state}
          // app: App
          super(props);
          this.state = Object.assign({
            status: 'Loaded.',
            confirmDeletion: true,
            path: [],
            selector: new Selector(),
            displayOnlySelected: false
          }, this.props.parameters);
          this.backendGroupVideos = this.backendGroupVideos.bind(this);
          this.changeGroup = this.changeGroup.bind(this);
          this.changePage = this.changePage.bind(this);
          this.classifierConcatenate = this.classifierConcatenate.bind(this);
          this.classifierSelectGroup = this.classifierSelectGroup.bind(this);
          this.classifierUnstack = this.classifierUnstack.bind(this);
          this.classifierReversePath = this.classifierReversePath.bind(this);
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
          this.scrollTop = this.scrollTop.bind(this);
          this.searchVideos = this.searchVideos.bind(this);
          this.selectAll = this.selectAll.bind(this);
          this.selectGroup = this.selectGroup.bind(this);
          this.selectVideos = this.selectVideos.bind(this);
          this.setPageSize = this.setPageSize.bind(this);
          this.sortVideos = this.sortVideos.bind(this);
          this.unselectVideos = this.unselectVideos.bind(this);
          this.updateStatus = this.updateStatus.bind(this);
          this.backend = this.backend.bind(this);
          this.findSimilarVideos = this.findSimilarVideos.bind(this);
          this.findSimilarVideosIgnoreCache = this.findSimilarVideosIgnoreCache.bind(this);
          this.closeDatabase = this.closeDatabase.bind(this);
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
          const groupDef = this.state.groupDef;
          const groupedByMoves = groupDef && groupDef.field === "move_id";
          const stringSetProperties = this.getStringSetProperties(this.state.properties);
          const stringProperties = this.getStringProperties(this.state.properties);
          const actions = this.features.actions;
          return /*#__PURE__*/React.createElement("div", {
            id: "videos",
            className: "vertical"
          }, /*#__PURE__*/React.createElement("header", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: "Options"
          }, /*#__PURE__*/React.createElement(Menu, {
            title: "Filter videos ..."
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.select
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.group
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.search
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.sort
          })), this.state.notFound || !nbVideos ? '' : /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.openRandomVideo
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.reload
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.manageProperties
          }), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.findSimilarVideos
          }, "Search similar videos"), /*#__PURE__*/React.createElement(Menu, {
            title: "Search similar videos (longer) ..."
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.findSimilarVideosIgnoreCache
          }, /*#__PURE__*/React.createElement("strong", null, "Ignore cache"))), stringSetProperties.length ? /*#__PURE__*/React.createElement(MenuItem, {
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
            action: () => this.backendGroupVideos(def.name, true)
          }, def.name))) : this.state.properties.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.backendGroupVideos(def.name, true)
          }, "Group videos by property: ", def.name)), /*#__PURE__*/React.createElement(Menu, {
            title: "Close database ..."
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.closeDatabase
          }, /*#__PURE__*/React.createElement("strong", null, "Close database")))), /*#__PURE__*/React.createElement("div", {
            className: "buttons"
          }), /*#__PURE__*/React.createElement("div", {
            className: "pagination text-right"
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
            className: "content horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "side-panel vertical"
          }, /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "filter",
            title: "Filter"
          }, this.renderFilter()), this.state.path.length ? /*#__PURE__*/React.createElement(Collapsable, {
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
          }, def.name))), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("button", {
            onClick: this.classifierReversePath
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
            groupDef: groupDef,
            isClassified: !!this.state.path.length,
            onSelect: this.selectGroup,
            onOptions: this.editPropertyValue,
            onPlus: groupDef.is_property && this.state.definitions[groupDef.field].multiple ? this.classifierSelectGroup : null
          })) : ''), /*#__PURE__*/React.createElement("div", {
            className: "main-panel videos"
          }, this.state.videos.map(data => /*#__PURE__*/React.createElement(Video, {
            key: data.video_id,
            data: data,
            propDefs: this.state.properties,
            selected: this.state.selector.has(data.video_id),
            onSelect: this.onVideoSelection,
            onSelectPropertyValue: this.focusPropertyValue,
            onInfo: this.updateStatus,
            confirmDeletion: this.state.confirmDeletion,
            groupedByMoves: groupedByMoves
          })))), /*#__PURE__*/React.createElement("footer", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "footer-status",
            onClick: this.resetStatus
          }, this.state.status), /*#__PURE__*/React.createElement("div", {
            className: "footer-information text-right"
          }, groupDef ? /*#__PURE__*/React.createElement("div", {
            className: "info group"
          }, "Group ", groupDef.group_id + 1, "/", groupDef.groups.length) : '', /*#__PURE__*/React.createElement("div", {
            className: "info count"
          }, nbVideos, " video", nbVideos > 1 ? 's' : ''), /*#__PURE__*/React.createElement("div", {
            className: "info size"
          }, validSize), /*#__PURE__*/React.createElement("div", {
            className: "info length"
          }, validLength))));
        }

        renderFilter() {
          const actions = this.features.actions;
          const sources = this.state.sources;
          const groupDef = this.state.groupDef;
          const searchDef = this.state.searchDef;
          const sorting = this.state.sorting;
          const realNbVideos = this.state.realNbVideos;
          const selectionSize = this.state.selector.size(realNbVideos);
          const sortingIsDefault = sorting.length === 1 && sorting[0] === '-date';
          const selectedAll = realNbVideos === selectionSize;
          return /*#__PURE__*/React.createElement("table", {
            className: "filter"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, sources.map((source, index) => /*#__PURE__*/React.createElement("div", {
            key: index
          }, source.join(' ').replace('_', ' ')))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.select
          })), !compareSources(window.PYTHON_DEFAULT_SOURCES, sources) ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.unselect
          })) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, groupDef ? /*#__PURE__*/React.createElement("div", null, "Grouped") : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, "Ungrouped")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.group,
            title: groupDef ? 'Edit ...' : 'Group ...'
          })), groupDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.ungroup
          })) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, "Searched ", SEARCH_TYPE_TITLE[searchDef.cond]), /*#__PURE__*/React.createElement("div", null, "\"", /*#__PURE__*/React.createElement("strong", null, searchDef.text), "\"")) : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, "No search")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.search,
            title: searchDef ? 'Edit ...' : 'Search ...'
          })), searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.unsearch
          })) : '')), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, "Sorted by"), sorting.map((val, i) => /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, val.substr(1)), ' ', val[0] === '-' ? /*#__PURE__*/React.createElement("span", null, "\u25BC") : /*#__PURE__*/React.createElement("span", null, "\u25B2")))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.sort
          })), sortingIsDefault ? '' : /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.unsort
          })))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, selectionSize ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, "Selected"), /*#__PURE__*/React.createElement("div", null, selectedAll ? 'all' : '', " ", selectionSize, " ", selectedAll ? '' : `/ ${realNbVideos}`, " ", "video", selectionSize < 2 ? '' : 's'), /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.displayOnlySelected
          }, this.state.displayOnlySelected ? 'Display all videos' : 'Display only selected videos'))) : /*#__PURE__*/React.createElement("div", null, "No videos selected"), selectedAll ? '' : /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.selectAll
          }, "select all")), selectionSize ? /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: "Edit property ..."
          }, this.state.properties.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.editPropertiesForManyVideos(def.name)
          }, def.name)))) : ''), /*#__PURE__*/React.createElement("td", null, selectionSize ? /*#__PURE__*/React.createElement(Cross, {
            title: `Deselect all`,
            action: this.deselect
          }) : ''))));
        }

        componentDidMount() {
          this.callbackIndex = KEYBOARD_MANAGER.register(this.features.onKeyPressed);
        }

        componentWillUnmount() {
          KEYBOARD_MANAGER.unregister(this.callbackIndex);
        }

        scrollTop() {
          document.querySelector('#videos .videos').scrollTop = 0;
        }

        backend(callargs, state, top = true) {
          const pageSize = state.pageSize !== undefined ? state.pageSize : this.state.pageSize;
          const pageNumber = state.pageNumber !== undefined ? state.pageNumber : this.state.pageNumber;
          const displayOnlySelected = state.displayOnlySelected !== undefined ? state.displayOnlySelected : this.state.displayOnlySelected;
          const selector = displayOnlySelected ? (state.selector !== undefined ? state.selector : this.state.selector).toJSON() : null;
          python_call("backend", callargs, pageSize, pageNumber, selector).then(info => this.setState(Object.assign(state, info), top ? this.scrollTop : undefined)).catch(backend_error);
        }

        onVideoSelection(videoID, selected) {
          const selector = this.state.selector.clone();

          if (selected) {
            selector.add(videoID);
            this.setState({
              selector
            });
          } else {
            selector.remove(videoID);
            if (this.state.displayOnlySelected) this.backend(null, {
              selector,
              displayOnlySelected: this.state.displayOnlySelected && selector.size(this.state.realNbVideos)
            });else this.setState({
              selector
            });
          }
        }

        deselect() {
          const selector = this.state.selector.clone();
          selector.clear();
          if (this.state.displayOnlySelected) this.backend(null, {
            selector,
            displayOnlySelected: false
          });else this.setState({
            selector
          });
        }

        selectAll() {
          // Should not be called if displayOnlySelected is true.
          const selector = this.state.selector.clone();
          selector.fill();
          if (this.state.displayOnlySelected) this.backend(null, {
            selector
          });else this.setState({
            selector
          });
        }

        displayOnlySelected() {
          this.backend(null, {
            displayOnlySelected: !this.state.displayOnlySelected
          });
        }

        updateStatus(status, reload = false, top = false) {
          if (reload) this.backend(null, {
            status
          }, top);else this.setState({
            status
          });
        }

        resetStatus() {
          this.setState({
            status: "Ready."
          });
        }

        unselectVideos() {
          this.backend(['set_sources', null], {
            pageNumber: 0
          });
        }

        selectVideos() {
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideosSource, {
            tree: SOURCE_TREE,
            sources: this.state.sources,
            onClose: sources => {
              this.backend(['set_sources', sources], {
                pageNumber: 0
              });
            }
          }));
        }

        groupVideos() {
          const groupDef = this.state.groupDef || {
            field: null,
            is_property: null,
            reverse: null
          };
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideosGrouping, {
            groupDef: groupDef,
            properties: this.state.properties,
            propertyMap: this.state.definitions,
            onClose: criterion => {
              this.backend(['set_groups', criterion.field, criterion.isProperty, criterion.sorting, criterion.reverse, criterion.allowSingletons], {
                pageNumber: 0
              });
            }
          }));
        }

        backendGroupVideos(field, isProperty = false, sorting = "count", reverse = true, allowSingletons = true) {
          this.backend(['set_groups', field, isProperty, sorting, reverse, allowSingletons], {
            pageNumber: 0
          });
        }

        editPropertiesForManyVideos(propertyName) {
          const selectionSize = this.state.selector.size(this.state.realNbVideos);
          const videoIndices = this.state.selector.toJSON();
          python_call('count_prop_values', propertyName, videoIndices).then(valuesAndCounts => Fancybox.load( /*#__PURE__*/React.createElement(FormSelectedVideosProperty, {
            nbVideos: selectionSize,
            definition: this.state.definitions[propertyName],
            values: valuesAndCounts,
            onClose: edition => {
              this.backend(['edit_property_for_videos', propertyName, videoIndices, edition.add, edition.remove], {
                pageNumber: 0,
                status: `Edited property "${propertyName}" for ${selectionSize} video${selectionSize < 2 ? '' : 's'}`
              });
            }
          }))).catch(backend_error);
        }

        searchVideos() {
          const search_def = this.state.searchDef || {
            text: null,
            cond: null
          };
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideosSearch, {
            text: search_def.text,
            cond: search_def.cond,
            onClose: criterion => {
              this.backend(['set_search', criterion.text, criterion.cond], {
                pageNumber: 0
              });
            }
          }));
        }

        sortVideos() {
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideosSort, {
            sorting: this.state.sorting,
            onClose: sorting => {
              this.backend(['set_sorting', sorting], {
                pageNumber: 0
              });
            }
          }));
        }

        resetGroup() {
          this.backend(['set_groups', ''], {
            pageNumber: 0
          });
        }

        resetSearch() {
          this.backend(['set_search', null, null], {
            pageNumber: 0
          });
        }

        resetSort() {
          this.backend(['set_sorting', null], {
            pageNumber: 0
          });
        }

        openRandomVideo() {
          python_call('open_random_video').then(filename => {
            this.setState({
              status: `Randomly opened: ${filename}`
            });
          }).catch(backend_error);
        }

        reloadDatabase() {
          this.props.app.dbUpdate();
        }

        findSimilarVideos() {
          this.props.app.dbFindSimilarities();
        }

        findSimilarVideosIgnoreCache() {
          this.props.app.dbFindSimilaritiesIgnoreCache();
        }

        manageProperties() {
          this.props.app.loadPropertiesPage();
        }

        fillWithKeywords() {
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideosKeywordsToProperty, {
            properties: this.getStringSetProperties(this.state.properties),
            onClose: state => {
              python_call('fill_property_with_terms', state.field, state.onlyEmpty).then(() => this.backend(null, {
                status: `Filled property "${state.field}" with video keywords.`
              })).catch(backend_error);
            }
          }));
        }

        setPageSize(count) {
          if (count !== this.state.pageSize) this.backend(null, {
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
          this.backend(['set_group', groupNumber], {
            pageNumber: 0
          });
        }

        selectGroup(value) {
          if (value === -1) this.resetGroup();else this.changeGroup(value);
        }

        changePage(pageNumber) {
          this.backend(null, {
            pageNumber
          });
        }

        getStringSetProperties(definitions) {
          return definitions.filter(def => def.multiple && def.type === "str");
        }

        getStringProperties(definitions) {
          return definitions.filter(def => def.type === "str");
        }
        /**
         * @param indicesSet {Set}
         */


        editPropertyValue(indicesSet) {
          const groupDef = this.state.groupDef;
          const name = groupDef.field;
          const values = [];
          const indices = Array.from(indicesSet);
          indices.sort();

          for (let index of indices) values.push(groupDef.groups[index].value);

          Fancybox.load( /*#__PURE__*/React.createElement(FormPropertySelectedValues, {
            properties: this.state.definitions,
            name: name,
            values: values,
            onClose: operation => {
              switch (operation.form) {
                case 'delete':
                  this.backend(['delete_property_value', name, values], {
                    status: `Property value deleted: "${name}" / "${values.join('", "')}"`
                  });
                  break;

                case 'edit':
                  this.backend(['edit_property_value', name, values, operation.value], {
                    status: `Property value edited: "${name}" : "${values.join('", "')}" -> "${operation.value}"`
                  });
                  break;

                case 'move':
                  this.backend(['move_property_value', name, values, operation.move], {
                    status: `Property value moved: "${values.join('", "')}" from "${name}" to "${operation.move}"`
                  });
                  break;
              }
            }
          }));
        }

        classifierReversePath() {
          python_call('classifier_reverse').then(path => this.setState({
            path
          })).catch(backend_error);
        }

        classifierSelectGroup(index) {
          this.backend(['classifier_select_group', index], {
            pageNumber: 0
          });
        }

        classifierUnstack() {
          this.backend(['classifier_back'], {
            pageNumber: 0
          });
        }

        classifierConcatenate(outputPropertyName) {
          this.backend(['classifier_concatenate_path', outputPropertyName], {
            pageNumber: 0
          });
        }

        focusPropertyValue(propertyName, propertyValue) {
          this.backend(['classifier_focus_prop_val', propertyName, propertyValue], {
            pageNumber: 0
          });
        }

        closeDatabase() {
          python_call("close_database").then(databases => this.props.app.dbHome(databases)).catch(backend_error);
        }

      });
    }
  };
});