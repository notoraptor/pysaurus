System.register(["../utils/constants.js", "../components/MenuPack.js", "../components/Pagination.js", "../components/Video.js", "../forms/FormVideosSource.js", "../forms/FormVideosGrouping.js", "../forms/FormVideosSearch.js", "../forms/FormVideosSort.js", "../components/GroupView.js", "../forms/FormPropertyEditSelectedValues.js", "../forms/FormVideosKeywordsToProperty.js", "../forms/FormSelectedVideosEditProperty.js", "../components/Collapsable.js", "../components/Cross.js", "../components/MenuItem.js", "../components/MenuItemCheck.js", "../components/MenuItemRadio.js", "../components/Menu.js", "../utils/Selector.js", "../utils/Action.js", "../utils/Actions.js", "../components/ActionToMenuItem.js", "../components/ActionToSettingIcon.js", "../components/ActionToCross.js", "../utils/backend.js", "../dialogs/FancyBox.js", "./HomePage.js", "../forms/FormDatabaseEditFolders.js", "../forms/FormDatabaseRename.js", "../dialogs/Dialog.js", "../components/Cell.js", "../forms/FormNewPredictionProperty.js", "../utils/functions.js"], function (_export, _context) {
  "use strict";

  var FIELD_MAP, PAGE_SIZES, SEARCH_TYPE_TITLE, SOURCE_TREE, MenuPack, Pagination, Video, FormVideosSource, FormVideosGrouping, FormVideosSearch, FormVideosSort, GroupView, FormPropertyEditSelectedValues, FormVideosKeywordsToProperty, FormSelectedVideosEditProperty, Collapsable, Cross, MenuItem, MenuItemCheck, MenuItemRadio, Menu, Selector, Action, Actions, ActionToMenuItem, ActionToSettingIcon, ActionToCross, backend_error, python_call, FancyBox, HomePage, FormDatabaseEditFolders, FormDatabaseRename, Dialog, Cell, FormNewPredictionProperty, formatString, VideosPage;

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

  function arrayEquals(a, b) {
    return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((val, index) => val === b[index]);
  }

  _export("VideosPage", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      FIELD_MAP = _utilsConstantsJs.FIELD_MAP;
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
    }, function (_formsFormPropertyEditSelectedValuesJs) {
      FormPropertyEditSelectedValues = _formsFormPropertyEditSelectedValuesJs.FormPropertyEditSelectedValues;
    }, function (_formsFormVideosKeywordsToPropertyJs) {
      FormVideosKeywordsToProperty = _formsFormVideosKeywordsToPropertyJs.FormVideosKeywordsToProperty;
    }, function (_formsFormSelectedVideosEditPropertyJs) {
      FormSelectedVideosEditProperty = _formsFormSelectedVideosEditPropertyJs.FormSelectedVideosEditProperty;
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
    }, function (_dialogsFancyBoxJs) {
      FancyBox = _dialogsFancyBoxJs.FancyBox;
    }, function (_HomePageJs) {
      HomePage = _HomePageJs.HomePage;
    }, function (_formsFormDatabaseEditFoldersJs) {
      FormDatabaseEditFolders = _formsFormDatabaseEditFoldersJs.FormDatabaseEditFolders;
    }, function (_formsFormDatabaseRenameJs) {
      FormDatabaseRename = _formsFormDatabaseRenameJs.FormDatabaseRename;
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }, function (_formsFormNewPredictionPropertyJs) {
      FormNewPredictionProperty = _formsFormNewPredictionPropertyJs.FormNewPredictionProperty;
    }, function (_utilsFunctionsJs) {
      formatString = _utilsFunctionsJs.formatString;
    }],
    execute: function () {
      _export("VideosPage", VideosPage = class VideosPage extends React.Component {
        constructor(props) {
          // parameters: {backend state}
          // app: App
          super(props);
          this.state = this.parametersToState({
            status: PYTHON_LANG.status_loaded,
            confirmDeletion: true,
            path: [],
            selector: new Selector(),
            displayOnlySelected: false,
            groupPageSize: 100,
            groupPageNumber: 0,
            groupSelection: new Set()
          }, this.props.parameters);
          this.backendGroupVideos = this.backendGroupVideos.bind(this);
          this.changeGroup = this.changeGroup.bind(this);
          this.changePage = this.changePage.bind(this);
          this.previousPage = this.previousPage.bind(this);
          this.nextPage = this.nextPage.bind(this);
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
          this.openRandomPlayer = this.openRandomPlayer.bind(this);
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
          this.moveVideo = this.moveVideo.bind(this);
          this.editDatabaseFolders = this.editDatabaseFolders.bind(this);
          this.renameDatabase = this.renameDatabase.bind(this);
          this.deleteDatabase = this.deleteDatabase.bind(this);
          this.onGroupViewState = this.onGroupViewState.bind(this);
          this.notify = this.notify.bind(this);
          this.canOpenRandomVideo = this.canOpenRandomVideo.bind(this);
          this.canOpenRandomPlayer = this.canOpenRandomPlayer.bind(this);
          this.canFindSimilarVideos = this.canFindSimilarVideos.bind(this);
          this.createPredictionProperty = this.createPredictionProperty.bind(this);
          this.populatePredictionProperty = this.populatePredictionProperty.bind(this);
          this.computePredictionProperty = this.computePredictionProperty.bind(this);
          this.applyPrediction = this.applyPrediction.bind(this);
          this.sourceIsSet = this.sourceIsSet.bind(this);
          this.groupIsSet = this.groupIsSet.bind(this);
          this.searchIsSet = this.searchIsSet.bind(this);
          this.sortIsSet = this.sortIsSet.bind(this);
          this.previousGroup = this.previousGroup.bind(this);
          this.nextGroup = this.nextGroup.bind(this);
          this.confirmAllUniqueMoves = this.confirmAllUniqueMoves.bind(this);
          this.callbackIndex = -1;
          this.notificationCallbackIndex = -1; // 14 shortcuts currently.

          this.features = new Actions({
            select: new Action("Ctrl+T", PYTHON_LANG.action_select_videos, this.selectVideos, Fancybox.isInactive),
            group: new Action("Ctrl+G", PYTHON_LANG.action_group_videos, this.groupVideos, Fancybox.isInactive),
            search: new Action("Ctrl+F", PYTHON_LANG.action_search_videos, this.searchVideos, Fancybox.isInactive),
            sort: new Action("Ctrl+S", PYTHON_LANG.action_sort_videos, this.sortVideos, Fancybox.isInactive),
            unselect: new Action("Ctrl+Shift+T", PYTHON_LANG.action_unselect_videos, this.unselectVideos, Fancybox.isInactive),
            ungroup: new Action("Ctrl+Shift+G", PYTHON_LANG.action_ungroup_videos, this.resetGroup, Fancybox.isInactive),
            unsearch: new Action("Ctrl+Shift+F", PYTHON_LANG.action_unsearch_videos, this.resetSearch, Fancybox.isInactive),
            unsort: new Action("Ctrl+Shift+S", PYTHON_LANG.action_unsort_videos, this.resetSort, Fancybox.isInactive),
            reload: new Action("Ctrl+R", PYTHON_LANG.action_reload_database, this.reloadDatabase, Fancybox.isInactive),
            manageProperties: new Action("Ctrl+P", PYTHON_LANG.action_manage_properties, this.manageProperties, Fancybox.isInactive),
            openRandomVideo: new Action("Ctrl+O", PYTHON_LANG.action_open_random_video, this.openRandomVideo, this.canOpenRandomVideo),
            openRandomPlayer: new Action("Ctrl+E", PYTHON_LANG.action_open_random_player, this.openRandomPlayer, this.canOpenRandomPlayer),
            previousPage: new Action("Ctrl+ArrowLeft", PYTHON_LANG.action_go_to_previous_page, this.previousPage, Fancybox.isInactive),
            nextPage: new Action("Ctrl+ArrowRight", PYTHON_LANG.action_go_to_next_page, this.nextPage, Fancybox.isInactive)
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
          const predictionProperties = this.getPredictionProperties(this.state.properties);
          const actions = this.features.actions;
          const aFilterIsSet = this.sourceIsSet() || this.groupIsSet() || this.searchIsSet() || this.sortIsSet();
          return /*#__PURE__*/React.createElement("div", {
            id: "videos",
            className: "absolute-plain p-4 vertical"
          }, /*#__PURE__*/React.createElement("header", {
            className: "horizontal flex-shrink-0"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: PYTHON_LANG.menu_database
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.reload
          }), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.renameDatabase
          }, formatString(PYTHON_LANG.action_rename_database, {
            name: this.state.database.name
          })), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.editDatabaseFolders
          }, formatString(PYTHON_LANG.action_edit_database_folders, {
            count: this.state.database.folders.length
          })), /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_close_database
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.closeDatabase
          }, /*#__PURE__*/React.createElement("strong", null, PYTHON_LANG.action_close_database))), /*#__PURE__*/React.createElement(MenuItem, {
            className: "red-flag",
            action: this.deleteDatabase
          }, PYTHON_LANG.action_delete_database)), /*#__PURE__*/React.createElement(MenuPack, {
            title: PYTHON_LANG.menu_videos
          }, /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_filter_videos
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.select
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.group
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.search
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.sort
          })), aFilterIsSet ? /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_reset_filters
          }, this.sourceIsSet() ? /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.unselect
          }) : "", this.groupIsSet() ? /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.ungroup
          }) : "", this.searchIsSet() ? /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.unsearch
          }) : "", this.sortIsSet() ? /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.unsort
          }) : "") : "", this.canOpenRandomVideo() ? /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.openRandomVideo
          }) : "", this.canOpenRandomPlayer() ? /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.openRandomPlayer
          }) : "", this.canFindSimilarVideos() ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.findSimilarVideos
          }, PYTHON_LANG.action_search_similar_videos) : "", this.canFindSimilarVideos() ? /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_search_similar_videos_longer
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.findSimilarVideosIgnoreCache
          }, /*#__PURE__*/React.createElement("strong", null, PYTHON_LANG.action_ignore_cache))) : "", groupedByMoves ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.confirmAllUniqueMoves
          }, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, PYTHON_LANG.action_confirm_all_unique_moves))) : ""), /*#__PURE__*/React.createElement(MenuPack, {
            title: PYTHON_LANG.menu_properties
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.manageProperties
          }), stringSetProperties.length ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.fillWithKeywords
          }, PYTHON_LANG.action_put_keywords_into_property) : "", this.state.properties.length > 5 ? /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_group_videos_by_property
          }, this.state.properties.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.backendGroupVideos(def.name, true)
          }, def.name))) : this.state.properties.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.backendGroupVideos(def.name, true)
          }, formatString(PYTHON_LANG.action_group_videos_by_property, {
            name: def.name
          })))), /*#__PURE__*/React.createElement(MenuPack, {
            title: PYTHON_LANG.menu_predictors
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.createPredictionProperty
          }, PYTHON_LANG.action_create_prediction_property), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.populatePredictionProperty
          }, PYTHON_LANG.action_populate_prediction_property_manually), predictionProperties.length ? /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_compute_prediction
          }, predictionProperties.map((def, i) => /*#__PURE__*/React.createElement(MenuItem, {
            key: i,
            action: () => this.computePredictionProperty(def.name)
          }, def.name))) : "", predictionProperties.length ? /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_apply_prediction
          }, predictionProperties.map((def, i) => /*#__PURE__*/React.createElement(MenuItem, {
            key: i,
            action: () => this.applyPrediction(def.name)
          }, def.name))) : ""), /*#__PURE__*/React.createElement(MenuPack, {
            title: PYTHON_LANG.menu_navigation
          }, /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_navigation_videos
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.previousPage
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.nextPage
          })), this.groupIsSet() ? /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_navigation_groups
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.previousGroup,
            shortcut: "Ctrl+ArrowUp"
          }, PYTHON_LANG.action_go_to_previous_group), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.nextGroup,
            shortcut: "Ctrl+ArrowDown"
          }, PYTHON_LANG.action_go_to_next_group)) : ""), /*#__PURE__*/React.createElement(MenuPack, {
            title: PYTHON_LANG.menu_options
          }, /*#__PURE__*/React.createElement(Menu, {
            title: PYTHON_LANG.menu_page_size
          }, PAGE_SIZES.map((count, index) => /*#__PURE__*/React.createElement(MenuItemRadio, {
            key: index,
            checked: this.state.pageSize === count,
            value: count,
            action: this.setPageSize
          }, formatString(PYTHON_LANG.action_page_size, {
            count
          })))), /*#__PURE__*/React.createElement(MenuItemCheck, {
            checked: this.state.confirmDeletion,
            action: this.confirmDeletionForNotFound
          }, PYTHON_LANG.action_confirm_deletion_for_entries_not_found)), /*#__PURE__*/React.createElement("div", {
            className: "pagination text-right"
          }, /*#__PURE__*/React.createElement(Pagination, {
            singular: PYTHON_LANG.word_page,
            plural: PYTHON_LANG.word_pages,
            nbPages: nbPages,
            pageNumber: this.state.pageNumber,
            key: this.state.pageNumber,
            onChange: this.changePage
          }))), /*#__PURE__*/React.createElement("div", {
            className: "frontier block flex-shrink-0"
          }), /*#__PURE__*/React.createElement("div", {
            className: "content position-relative flex-grow-1"
          }, /*#__PURE__*/React.createElement("div", {
            className: "absolute-plain horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "side-panel vertical"
          }, /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "filter flex-shrink-0",
            title: PYTHON_LANG.section_filter
          }, this.renderFilter()), this.state.path.length ? /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "filter flex-shrink-0",
            title: PYTHON_LANG.section_classifier_path
          }, stringProperties.length ? /*#__PURE__*/React.createElement("div", {
            className: "path-menu text-center p-2"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: PYTHON_LANG.menu_concatenate_path
          }, stringProperties.map((def, i) => /*#__PURE__*/React.createElement(MenuItem, {
            key: i,
            action: () => this.classifierConcatenate(def.name)
          }, def.name))), /*#__PURE__*/React.createElement("div", {
            className: "pt-2"
          }, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.classifierReversePath
          }, PYTHON_LANG.action_reverse_path))) : "", this.state.path.map((value, index) => /*#__PURE__*/React.createElement("div", {
            key: index,
            className: "path-step horizontal px-2 py-1"
          }, /*#__PURE__*/React.createElement("div", {
            className: "flex-grow-1"
          }, value.toString()), index === this.state.path.length - 1 ? /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, /*#__PURE__*/React.createElement(Cross, {
            title: PYTHON_LANG.text_unstack,
            action: this.classifierUnstack
          })) : ""))) : "", groupDef ? /*#__PURE__*/React.createElement("div", {
            className: "flex-grow-1 position-relative"
          }, /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "group absolute-plain vertical",
            title: PYTHON_LANG.section_groups
          }, /*#__PURE__*/React.createElement(GroupView, {
            groupDef: groupDef,
            isClassified: !!this.state.path.length,
            pageSize: this.state.groupPageSize,
            pageNumber: this.state.groupPageNumber,
            selection: this.state.groupSelection,
            onGroupViewState: this.onGroupViewState,
            onOptions: this.editPropertyValue,
            onPlus: groupDef.is_property && this.state.definitions[groupDef.field].multiple ? this.classifierSelectGroup : null
          }))) : ""), /*#__PURE__*/React.createElement("div", {
            className: "main-panel videos overflow-auto"
          }, this.state.videos.map(data => /*#__PURE__*/React.createElement(Video, {
            key: data.video_id,
            data: data,
            propDefs: this.state.properties,
            groupDef: groupDef,
            selected: this.state.selector.has(data.video_id),
            onSelect: this.onVideoSelection,
            onMove: this.moveVideo,
            onSelectPropertyValue: this.focusPropertyValue,
            onInfo: this.updateStatus,
            confirmDeletion: this.state.confirmDeletion,
            groupedByMoves: groupedByMoves
          }))))), /*#__PURE__*/React.createElement("footer", {
            className: "horizontal flex-shrink-0"
          }, /*#__PURE__*/React.createElement("div", {
            className: "footer-status clickable",
            title: this.state.status,
            onClick: this.resetStatus
          }, this.state.status), /*#__PURE__*/React.createElement("div", {
            className: "footer-information text-right"
          }, groupDef ? /*#__PURE__*/React.createElement("div", {
            className: "info group"
          }, groupDef.groups.length ? formatString(PYTHON_LANG.text_group, {
            group: groupDef.group_id + 1,
            count: groupDef.groups.length
          }) : PYTHON_LANG.text_no_group) : "", /*#__PURE__*/React.createElement("div", {
            className: "info count"
          }, nbVideos, " video", nbVideos > 1 ? 's' : ""), /*#__PURE__*/React.createElement("div", {
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
            className: "filter w-100"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, sources.map((source, index) => /*#__PURE__*/React.createElement("div", {
            key: index
          }, source.join(" ").replace('_', " ")))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.select
          })), !compareSources(window.PYTHON_DEFAULT_SOURCES, sources) ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.unselect
          })) : "")), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, groupDef ? /*#__PURE__*/React.createElement("div", null, PYTHON_LANG.text_grouped) : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, PYTHON_LANG.text_ungrouped)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.group,
            title: groupDef ? PYTHON_LANG.action_edit : PYTHON_LANG.action_group
          })), groupDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.ungroup
          })) : "")), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, formatString(PYTHON_LANG.text_searched, {
            text: SEARCH_TYPE_TITLE[searchDef.cond]
          })), /*#__PURE__*/React.createElement("div", {
            className: "word-break-all"
          }, "\"", /*#__PURE__*/React.createElement("strong", null, searchDef.text), "\"")) : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, PYTHON_LANG.text_no_search)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.search,
            title: searchDef ? PYTHON_LANG.action_edit : PYTHON_LANG.action_search
          })), searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.unsearch
          })) : "")), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, PYTHON_LANG.text_sorted_by), sorting.map((val, i) => /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, FIELD_MAP.fields[val.substr(1)].title), " ", val[0] === '-' ? /*#__PURE__*/React.createElement("span", null, "\u25BC") : /*#__PURE__*/React.createElement("span", null, "\u25B2")))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.sort
          })), sortingIsDefault ? "" : /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.unsort
          })))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, selectionSize ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, "Selected"), /*#__PURE__*/React.createElement("div", null, selectedAll ? formatString(PYTHON_LANG.text_all_videos_selected, {
            count: selectionSize
          }) : formatString(PYTHON_LANG.text_videos_selected, {
            count: selectionSize,
            total: realNbVideos
          })), /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.displayOnlySelected
          }, this.state.displayOnlySelected ? PYTHON_LANG.action_display_all_videos : PYTHON_LANG.action_display_selected_videos))) : /*#__PURE__*/React.createElement("div", null, PYTHON_LANG.text_no_videos_selected), selectedAll ? "" : /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.selectAll
          }, PYTHON_LANG.action_select_all)), selectionSize ? /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: PYTHON_LANG.menu_edit_properties
          }, this.state.properties.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.editPropertiesForManyVideos(def.name)
          }, def.name)))) : ""), /*#__PURE__*/React.createElement("td", null, selectionSize ? /*#__PURE__*/React.createElement(Cross, {
            title: PYTHON_LANG.action_deselect_all,
            action: this.deselect
          }) : ""))));
        }

        createPredictionProperty() {
          Fancybox.load( /*#__PURE__*/React.createElement(FormNewPredictionProperty, {
            onClose: name => {
              this.backend(["create_prediction_property", name]);
            }
          }));
        }

        populatePredictionProperty() {
          Fancybox.load( /*#__PURE__*/React.createElement(FancyBox, {
            title: PYTHON_LANG.form_title_populate_predictor_manually
          }, markdownToReact(PYTHON_LANG.form_content_populate_predictor_manually)));
        }

        computePredictionProperty(propName) {
          this.props.app.dbUpdate("compute_predictor", propName);
        }

        applyPrediction(propName) {
          this.props.app.dbUpdate("apply_predictor", propName);
        }

        sourceIsSet() {
          return !compareSources(window.PYTHON_DEFAULT_SOURCES, this.state.sources);
        }

        groupIsSet() {
          return !!this.state.groupDef;
        }

        searchIsSet() {
          return !!this.state.searchDef;
        }

        sortIsSet() {
          return !(this.state.sorting.length === 1 && this.state.sorting[0] === '-date');
        }

        canOpenRandomVideo() {
          return Fancybox.isInactive() && !this.state.notFound && this.state.nbVideos;
        }

        canOpenRandomPlayer() {
          return Fancybox.isInactive() && window.PYTHON_HAS_EMBEDDED_PLAYER && this.canOpenRandomVideo();
        }

        canFindSimilarVideos() {
          return window.PYTHON_FEATURE_COMPARISON;
        }

        componentDidMount() {
          this.callbackIndex = KEYBOARD_MANAGER.register(this.features.onKeyPressed);
          this.notificationCallbackIndex = NOTIFICATION_MANAGER.register(this.notify);
        }

        componentWillUnmount() {
          KEYBOARD_MANAGER.unregister(this.callbackIndex);
          NOTIFICATION_MANAGER.unregister(this.notificationCallbackIndex);
        }

        backend(callargs, state = {}, top = true) {
          const pageSize = state.pageSize !== undefined ? state.pageSize : this.state.pageSize;
          const pageNumber = state.pageNumber !== undefined ? state.pageNumber : this.state.pageNumber;
          const displayOnlySelected = state.displayOnlySelected !== undefined ? state.displayOnlySelected : this.state.displayOnlySelected;
          const selector = displayOnlySelected ? (state.selector !== undefined ? state.selector : this.state.selector).toJSON() : null;
          if (!state.status) state.status = PYTHON_LANG.status_updated;
          python_call("backend", callargs, pageSize, pageNumber, selector).then(info => this.setState(this.parametersToState(state, info), top ? this.scrollTop : undefined)).catch(backend_error);
        }

        parametersToState(state, info) {
          if (info.groupDef) {
            const groupPageSize = state.groupPageSize !== undefined ? state.groupPageSize : this.state.groupPageSize;
            const groupPageNumber = state.groupPageNumber !== undefined ? state.groupPageNumber : this.state.groupPageNumber;
            const count = info.groupDef.groups.length;
            const nbPages = Math.floor(count / groupPageSize) + (count % groupPageSize ? 1 : 0);
            state.groupPageNumber = Math.min(Math.max(0, groupPageNumber), nbPages - 1);
          }

          if (info.viewChanged && !state.selector) state.selector = new Selector();
          return Object.assign(state, info);
        }

        notify(notification) {
          if (notification.name === "NextRandomVideo") this.backend(null, {});
        }

        onGroupViewState(groupState) {
          const state = {};
          if (groupState.hasOwnProperty("pageSize")) state.groupPageSize = groupState.pageSize;
          if (groupState.hasOwnProperty("pageNumber")) state.groupPageNumber = groupState.pageNumber;
          if (groupState.hasOwnProperty("selection")) state.groupSelection = groupState.selection;
          const groupID = groupState.hasOwnProperty("groupID") ? groupState.groupID : null;
          this.setState(state, groupID === null ? undefined : () => this.selectGroup(groupID));
        }

        scrollTop() {
          document.querySelector('#videos .videos').scrollTop = 0;
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

        moveVideo(videoID, directory) {
          Fancybox.load( /*#__PURE__*/React.createElement(FancyBox, {
            title: formatString(PYTHON_LANG.form_title_move_file, {
              path: directory
            }),
            onClose: () => {
              python_call("cancel_copy");
            }
          }, /*#__PURE__*/React.createElement("div", {
            className: "absolute-plain vertical"
          }, /*#__PURE__*/React.createElement(HomePage, {
            key: window.APP_STATE.idGenerator.next(),
            app: this.props.app,
            parameters: {
              command: ["move_video_file", videoID, directory],
              onReady: status => {
                Fancybox.close();
                if (status === "Cancelled") this.updateStatus(PYTHON_LANG.status_video_not_moved);else this.updateStatus(formatString(PYTHON_LANG.status_video_moved, {
                  directory
                }), true);
              }
            }
          }))));
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
            status: PYTHON_LANG.status_ready
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
          python_call('count_prop_values', propertyName, videoIndices).then(valuesAndCounts => Fancybox.load( /*#__PURE__*/React.createElement(FormSelectedVideosEditProperty, {
            nbVideos: selectionSize,
            definition: this.state.definitions[propertyName],
            values: valuesAndCounts,
            onClose: edition => {
              this.backend(['edit_property_for_videos', propertyName, videoIndices, edition.add, edition.remove], {
                pageNumber: 0,
                status: formatString(PYTHON_LANG.status_prop_val_edited, {
                  property: propertyName,
                  count: selectionSize
                })
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

        editDatabaseFolders() {
          Fancybox.load( /*#__PURE__*/React.createElement(FormDatabaseEditFolders, {
            database: this.state.database,
            onClose: paths => {
              python_call("set_video_folders", paths).then(() => this.props.app.dbUpdate("update_database")).catch(backend_error);
            }
          }));
        }

        renameDatabase() {
          Fancybox.load( /*#__PURE__*/React.createElement(FormDatabaseRename, {
            title: this.state.database.name,
            onClose: name => {
              this.backend(["rename_database", name], {
                pageNumber: 0
              });
            }
          }));
        }

        deleteDatabase() {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: formatString(PYTHON_LANG.dialog_delete_database, {
              name: this.state.database.name
            }),
            yes: PYTHON_LANG.text_delete,
            action: () => {
              python_call("delete_database").then(databases => this.props.app.dbHome(databases)).catch(backend_error);
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            center: true,
            full: true,
            className: "text-center"
          }, /*#__PURE__*/React.createElement("h1", null, PYTHON_LANG.text_database, " ", /*#__PURE__*/React.createElement("span", {
            className: "red-flag"
          }, this.state.database.name)), markdownToReact(PYTHON_LANG.form_content_confirm_delete_database))));
        }

        confirmAllUniqueMoves() {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: PYTHON_LANG.action_confirm_all_unique_moves,
            yes: PYTHON_LANG.text_move,
            action: () => {
              python_call("confirm_unique_moves").then(nbMoved => this.updateStatus(`Moved ${nbMoved} video(s)`, true, true)).catch(backend_error);
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            center: true,
            full: true,
            className: "text-center"
          }, markdownToReact(PYTHON_LANG.form_content_confirm_unique_moves))));
        }

        resetGroup() {
          this.backend(['set_groups', ""], {
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
            this.updateStatus(formatString(PYTHON_LANG.status_randomly_opened, {
              path: filename
            }), true, true);
          }).catch(backend_error);
        }

        openRandomPlayer() {
          python_call('open_random_player').then(() => this.updateStatus("Random player opened!", true, true)).catch(backend_error);
        }

        reloadDatabase() {
          this.props.app.dbUpdate("update_database");
        }

        findSimilarVideos() {
          this.props.app.dbUpdate("find_similar_videos");
        }

        findSimilarVideosIgnoreCache() {
          this.props.app.dbUpdate("find_similar_videos_ignore_cache");
        }

        manageProperties() {
          this.props.app.loadPropertiesPage();
        }

        fillWithKeywords() {
          Fancybox.load( /*#__PURE__*/React.createElement(FormVideosKeywordsToProperty, {
            properties: this.getStringSetProperties(this.state.properties),
            onClose: state => {
              python_call('fill_property_with_terms', state.field, state.onlyEmpty).then(() => this.backend(null, {
                status: formatString(PYTHON_LANG.status_filled_property_with_keywords, {
                  name: state.field
                })
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

        previousPage() {
          const pageNumber = this.state.pageNumber - 1;
          if (pageNumber >= 0) this.changePage(pageNumber);
        }

        nextPage() {
          const pageNumber = this.state.pageNumber + 1;
          if (pageNumber < this.state.nbPages) this.changePage(pageNumber);
        }

        previousGroup() {
          const groupID = this.state.groupDef.group_id;
          if (groupID > 0) this.onGroupViewState({
            groupID: groupID - 1
          });
        }

        nextGroup() {
          const groupID = this.state.groupDef.group_id;
          if (groupID < this.state.groupDef.groups.length - 1) this.onGroupViewState({
            groupID: groupID + 1
          });
        }

        getStringSetProperties(definitions) {
          return definitions.filter(def => def.multiple && def.type === "str");
        }

        getStringProperties(definitions) {
          return definitions.filter(def => def.type === "str");
        }

        getPredictionProperties(definitions) {
          return definitions.filter(def => def.name.indexOf("<?") === 0 && def.name.indexOf(">") === def.name.length - 1 && def.type === "int" && def.defaultValue === -1 && !def.multiple && arrayEquals(def.enumeration, [-1, 0, 1]));
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

          Fancybox.load( /*#__PURE__*/React.createElement(FormPropertyEditSelectedValues, {
            properties: this.state.definitions,
            name: name,
            values: values,
            onClose: operation => {
              switch (operation.form) {
                case 'delete':
                  this.backend(['delete_property_value', name, values], {
                    groupSelection: new Set(),
                    status: formatString(PYTHON_LANG.status_prop_vals_deleted, {
                      name: name,
                      values: values.join('", "')
                    })
                  });
                  break;

                case 'edit':
                  this.backend(['edit_property_value', name, values, operation.value], {
                    groupSelection: new Set(),
                    status: formatString(PYTHON_LANG.status_prop_vals_edited, {
                      name: name,
                      values: values.join('", "'),
                      destination: operation.value
                    })
                  });
                  break;

                case 'move':
                  this.backend(['move_property_value', name, values, operation.move], {
                    groupSelection: new Set(),
                    status: formatString(PYTHON_LANG.status_prop_val_moved, {
                      values: values.join('", "'),
                      name: name,
                      destination: operation.move
                    })
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