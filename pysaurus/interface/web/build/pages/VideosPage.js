System.register(["../utils/constants.js", "../components/MenuPack.js", "../components/Pagination.js", "../components/Video.js", "../forms/FormVideosSource.js", "../forms/FormVideosGrouping.js", "../forms/FormVideosSearch.js", "../forms/FormVideosSort.js", "../components/GroupView.js", "../forms/FormPropertyEditSelectedValues.js", "../forms/FormVideosKeywordsToProperty.js", "../forms/FormSelectedVideosEditProperty.js", "../components/Collapsable.js", "../components/Cross.js", "../components/MenuItem.js", "../components/MenuItemCheck.js", "../components/MenuItemRadio.js", "../components/Menu.js", "../utils/Selector.js", "../utils/Action.js", "../utils/Actions.js", "../components/ActionToMenuItem.js", "../components/ActionToSettingIcon.js", "../components/ActionToCross.js", "../utils/backend.js", "../dialogs/FancyBox.js", "./HomePage.js", "../forms/FormDatabaseEditFolders.js", "../dialogs/Dialog.js", "../components/Cell.js", "../forms/FormNewPredictionProperty.js", "../forms/GenericFormRename.js", "../language.js", "../utils/functions.js"], function (_export, _context) {
  "use strict";

  var getFieldMap, PAGE_SIZES, SOURCE_TREE, MenuPack, Pagination, Video, FormVideosSource, FormVideosGrouping, FormVideosSearch, FormVideosSort, GroupView, FormPropertyEditSelectedValues, FormVideosKeywordsToProperty, FormSelectedVideosEditProperty, Collapsable, Cross, MenuItem, MenuItemCheck, MenuItemRadio, Menu, Selector, Action, Actions, ActionToMenuItem, ActionToSettingIcon, ActionToCross, backend_error, python_call, FancyBox, HomePage, FormDatabaseEditFolders, Dialog, Cell, FormNewPredictionProperty, GenericFormRename, LangContext, arrayEquals, VideosPage;

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
      getFieldMap = _utilsConstantsJs.getFieldMap;
      PAGE_SIZES = _utilsConstantsJs.PAGE_SIZES;
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
    }, function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }, function (_formsFormNewPredictionPropertyJs) {
      FormNewPredictionProperty = _formsFormNewPredictionPropertyJs.FormNewPredictionProperty;
    }, function (_formsGenericFormRenameJs) {
      GenericFormRename = _formsGenericFormRenameJs.GenericFormRename;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
    }, function (_utilsFunctionsJs) {
      arrayEquals = _utilsFunctionsJs.arrayEquals;
    }],
    execute: function () {
      _export("VideosPage", VideosPage = class VideosPage extends React.Component {
        constructor(props) {
          // parameters: {backend state}
          // app: App
          super(props);
          this.state = this.parametersToState({
            status: undefined,
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
          this.getStatus = this.getStatus.bind(this);
          this.getFields = this.getFields.bind(this);
          this.getActions = this.getActions.bind(this);
          this.playlist = this.playlist.bind(this);
          this.callbackIndex = -1;
          this.notificationCallbackIndex = -1;
        }

        render() {
          const languages = this.props.app.getLanguages();
          const nbVideos = this.state.nbVideos;
          const nbPages = this.state.nbPages;
          const validSize = this.state.validSize;
          const validLength = this.state.validLength;
          const groupDef = this.state.groupDef;
          const groupedByMoves = groupDef && groupDef.field === "move_id";
          const stringSetProperties = this.getStringSetProperties(this.state.prop_types);
          const stringProperties = this.getStringProperties(this.state.prop_types);
          const predictionProperties = this.getPredictionProperties(this.state.prop_types);
          const actions = this.getActions().actions;
          const aFilterIsSet = this.sourceIsSet() || this.groupIsSet() || this.searchIsSet() || this.sortIsSet();
          const status = this.getStatus();
          return /*#__PURE__*/React.createElement("div", {
            id: "videos",
            className: "absolute-plain p-4 vertical"
          }, /*#__PURE__*/React.createElement("header", {
            className: "horizontal flex-shrink-0"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: this.context.menu_database
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.reload
          }), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.renameDatabase
          }, this.context.action_rename_database.format({
            name: this.state.database.name
          })), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.editDatabaseFolders
          }, this.context.action_edit_database_folders.format({
            count: this.state.database.folders.length
          })), /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_close_database
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.closeDatabase
          }, /*#__PURE__*/React.createElement("strong", null, this.context.action_close_database))), /*#__PURE__*/React.createElement(MenuItem, {
            className: "red-flag",
            action: this.deleteDatabase
          }, this.context.action_delete_database)), /*#__PURE__*/React.createElement(MenuPack, {
            title: this.context.menu_videos
          }, /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_filter_videos
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.select
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.group
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.search
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.sort
          })), aFilterIsSet ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_reset_filters
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
          }, this.context.action_search_similar_videos) : "", this.canFindSimilarVideos() ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_search_similar_videos_longer
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.findSimilarVideosIgnoreCache
          }, /*#__PURE__*/React.createElement("strong", null, this.context.action_ignore_cache))) : "", groupedByMoves ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.confirmAllUniqueMoves
          }, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, this.context.action_confirm_all_unique_moves))) : "", /*#__PURE__*/React.createElement(MenuItem, {
            action: this.playlist,
            shortcut: "Ctrl+L"
          }, /*#__PURE__*/React.createElement("strong", null, /*#__PURE__*/React.createElement("em", null, "Play list")))), /*#__PURE__*/React.createElement(MenuPack, {
            title: this.context.menu_properties
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.manageProperties
          }), stringSetProperties.length ? /*#__PURE__*/React.createElement(MenuItem, {
            action: this.fillWithKeywords
          }, this.context.action_put_keywords_into_property) : "", this.state.prop_types.length > 5 ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_group_videos_by_property
          }, this.state.prop_types.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.backendGroupVideos(def.name, true)
          }, def.name))) : this.state.prop_types.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.backendGroupVideos(def.name, true)
          }, this.context.action_group_videos_by_property.format({
            name: def.name
          }))), stringProperties.length ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.text_convert_to_lowercase
          }, stringProperties.map((def, defIndex) => /*#__PURE__*/React.createElement(MenuItem, {
            key: defIndex,
            action: () => this.propToLowercase(def)
          }, def.name))) : "", stringProperties.length ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.text_convert_to_uppercase
          }, stringProperties.map((def, defIndex) => /*#__PURE__*/React.createElement(MenuItem, {
            key: defIndex,
            action: () => this.propToUppercase(def)
          }, def.name))) : ""), /*#__PURE__*/React.createElement(MenuPack, {
            title: this.context.menu_predictors
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.createPredictionProperty
          }, this.context.action_create_prediction_property), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.populatePredictionProperty
          }, this.context.action_populate_prediction_property_manually), predictionProperties.length ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_compute_prediction
          }, predictionProperties.map((def, i) => /*#__PURE__*/React.createElement(MenuItem, {
            key: i,
            action: () => this.computePredictionProperty(def.name)
          }, def.name))) : "", predictionProperties.length ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_apply_prediction
          }, predictionProperties.map((def, i) => /*#__PURE__*/React.createElement(MenuItem, {
            key: i,
            action: () => this.applyPrediction(def.name)
          }, def.name))) : ""), /*#__PURE__*/React.createElement(MenuPack, {
            title: this.context.menu_navigation
          }, /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_navigation_videos
          }, /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.previousPage
          }), /*#__PURE__*/React.createElement(ActionToMenuItem, {
            action: actions.nextPage
          })), this.groupIsSet() ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_navigation_groups
          }, /*#__PURE__*/React.createElement(MenuItem, {
            action: this.previousGroup,
            shortcut: "Ctrl+ArrowUp"
          }, this.context.action_go_to_previous_group), /*#__PURE__*/React.createElement(MenuItem, {
            action: this.nextGroup,
            shortcut: "Ctrl+ArrowDown"
          }, this.context.action_go_to_next_group)) : ""), /*#__PURE__*/React.createElement(MenuPack, {
            title: this.context.menu_options
          }, /*#__PURE__*/React.createElement(Menu, {
            title: this.context.menu_page_size
          }, PAGE_SIZES.map((count, index) => /*#__PURE__*/React.createElement(MenuItemRadio, {
            key: index,
            checked: this.state.pageSize === count,
            value: count,
            action: this.setPageSize
          }, this.context.action_page_size.format({
            count
          })))), /*#__PURE__*/React.createElement(MenuItemCheck, {
            checked: this.state.confirmDeletion,
            action: this.confirmDeletionForNotFound
          }, this.context.action_confirm_deletion_for_entries_not_found), languages.length > 1 ? /*#__PURE__*/React.createElement(Menu, {
            title: this.context.text_choose_language + " ..."
          }, languages.map((language, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.props.app.setLanguage(language.name)
          }, this.context.__language__ === language.name ? /*#__PURE__*/React.createElement("strong", null, language.name) : language.name))) : ""), /*#__PURE__*/React.createElement("div", {
            className: "pagination text-right"
          }, /*#__PURE__*/React.createElement(Pagination, {
            singular: this.context.word_page,
            plural: this.context.word_pages,
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
            title: this.context.section_filter
          }, this.renderFilter()), this.state.path.length ? /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "filter flex-shrink-0",
            title: this.context.section_classifier_path
          }, stringProperties.length ? /*#__PURE__*/React.createElement("div", {
            className: "path-menu text-center p-2"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: this.context.menu_concatenate_path
          }, stringProperties.map((def, i) => /*#__PURE__*/React.createElement(MenuItem, {
            key: i,
            action: () => this.classifierConcatenate(def.name)
          }, def.name))), /*#__PURE__*/React.createElement("div", {
            className: "pt-2"
          }, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.classifierReversePath
          }, this.context.action_reverse_path))) : "", this.state.path.map((value, index) => /*#__PURE__*/React.createElement("div", {
            key: index,
            className: "path-step horizontal px-2 py-1"
          }, /*#__PURE__*/React.createElement("div", {
            className: "flex-grow-1"
          }, value.toString()), index === this.state.path.length - 1 ? /*#__PURE__*/React.createElement("div", {
            className: "icon"
          }, /*#__PURE__*/React.createElement(Cross, {
            title: this.context.text_unstack,
            action: this.classifierUnstack
          })) : ""))) : "", groupDef ? /*#__PURE__*/React.createElement("div", {
            className: "flex-grow-1 position-relative"
          }, /*#__PURE__*/React.createElement(Collapsable, {
            lite: false,
            className: "group absolute-plain vertical",
            title: this.context.section_groups
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
            propDefs: this.state.prop_types,
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
            title: status,
            onClick: this.resetStatus
          }, status), /*#__PURE__*/React.createElement("div", {
            className: "footer-information text-right"
          }, groupDef ? /*#__PURE__*/React.createElement("div", {
            className: "info group"
          }, groupDef.groups.length ? this.context.text_group.format({
            group: groupDef.group_id + 1,
            count: groupDef.groups.length
          }) : this.context.text_no_group) : "", /*#__PURE__*/React.createElement("div", {
            className: "info count"
          }, nbVideos, " video", nbVideos > 1 ? 's' : ""), /*#__PURE__*/React.createElement("div", {
            className: "info size"
          }, validSize), /*#__PURE__*/React.createElement("div", {
            className: "info length"
          }, validLength))));
        }

        renderFilter() {
          const searchTypeTitle = {
            exact: this.context.search_exact,
            and: this.context.search_and,
            or: this.context.search_or,
            id: this.context.search_id
          };
          const actions = this.getActions().actions;
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
          })) : "")), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, groupDef ? /*#__PURE__*/React.createElement("div", null, this.context.text_grouped) : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, this.context.text_ungrouped)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.group,
            title: groupDef ? this.context.action_edit : this.context.action_group
          })), groupDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.ungroup
          })) : "")), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, this.context.text_searched.format({
            text: searchTypeTitle[searchDef.cond]
          })), /*#__PURE__*/React.createElement("div", {
            className: "word-break-all"
          }, "\"", /*#__PURE__*/React.createElement("strong", null, searchDef.text), "\"")) : /*#__PURE__*/React.createElement("div", {
            className: "no-filter"
          }, this.context.text_no_search)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.search,
            title: searchDef ? this.context.action_edit : this.context.action_search
          })), searchDef ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.unsearch
          })) : "")), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, this.context.text_sorted_by), sorting.map((val, i) => /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, this.getFields().fields[val.substr(1)].title), " ", val[0] === '-' ? /*#__PURE__*/React.createElement("span", null, "\u25BC") : /*#__PURE__*/React.createElement("span", null, "\u25B2")))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToSettingIcon, {
            action: actions.sort
          })), sortingIsDefault ? "" : /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(ActionToCross, {
            action: actions.unsort
          })))), /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, selectionSize ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, "Selected"), /*#__PURE__*/React.createElement("div", null, selectedAll ? this.context.text_all_videos_selected.format({
            count: selectionSize
          }) : this.context.text_videos_selected.format({
            count: selectionSize,
            total: realNbVideos
          })), /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.displayOnlySelected
          }, this.state.displayOnlySelected ? this.context.action_display_all_videos : this.context.action_display_selected_videos))) : /*#__PURE__*/React.createElement("div", null, this.context.text_no_videos_selected), selectedAll ? "" : /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.selectAll
          }, this.context.action_select_all)), selectionSize ? /*#__PURE__*/React.createElement("div", {
            className: "mb-1"
          }, /*#__PURE__*/React.createElement(MenuPack, {
            title: this.context.menu_edit_properties
          }, this.state.prop_types.map((def, index) => /*#__PURE__*/React.createElement(MenuItem, {
            key: index,
            action: () => this.editPropertiesForManyVideos(def.name)
          }, def.name)))) : ""), /*#__PURE__*/React.createElement("td", null, selectionSize ? /*#__PURE__*/React.createElement(Cross, {
            title: this.context.action_deselect_all,
            action: this.deselect
          }) : ""))));
        }

        getStatus() {
          return this.state.status === undefined ? this.context.status_loaded : this.state.status;
        }

        getFields() {
          return getFieldMap(this.context);
        }

        getActions() {
          // 14 shortcuts currently.
          return new Actions({
            select: new Action("Ctrl+T", this.context.action_select_videos, this.selectVideos, Fancybox.isInactive),
            group: new Action("Ctrl+G", this.context.action_group_videos, this.groupVideos, Fancybox.isInactive),
            search: new Action("Ctrl+F", this.context.action_search_videos, this.searchVideos, Fancybox.isInactive),
            sort: new Action("Ctrl+S", this.context.action_sort_videos, this.sortVideos, Fancybox.isInactive),
            unselect: new Action("Ctrl+Shift+T", this.context.action_unselect_videos, this.unselectVideos, Fancybox.isInactive),
            ungroup: new Action("Ctrl+Shift+G", this.context.action_ungroup_videos, this.resetGroup, Fancybox.isInactive),
            unsearch: new Action("Ctrl+Shift+F", this.context.action_unsearch_videos, this.resetSearch, Fancybox.isInactive),
            unsort: new Action("Ctrl+Shift+S", this.context.action_unsort_videos, this.resetSort, Fancybox.isInactive),
            reload: new Action("Ctrl+R", this.context.action_reload_database, this.reloadDatabase, Fancybox.isInactive),
            manageProperties: new Action("Ctrl+P", this.context.action_manage_properties, this.manageProperties, Fancybox.isInactive),
            openRandomVideo: new Action("Ctrl+O", this.context.action_open_random_video, this.openRandomVideo, this.canOpenRandomVideo),
            openRandomPlayer: new Action("Ctrl+E", this.context.action_open_random_player, this.openRandomPlayer, this.canOpenRandomPlayer),
            previousPage: new Action("Ctrl+ArrowLeft", this.context.action_go_to_previous_page, this.previousPage, Fancybox.isInactive),
            nextPage: new Action("Ctrl+ArrowRight", this.context.action_go_to_next_page, this.nextPage, Fancybox.isInactive),
            playlist: new Action("Ctrl+L", "play list", this.playlist, Fancybox.isInactive)
          }, this.context);
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
            title: this.context.form_title_populate_predictor_manually
          }, this.context.form_content_populate_predictor_manually.markdown()));
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
          return Fancybox.isInactive() && !this.state.notFound && this.state.totalNbVideos;
        }

        canOpenRandomPlayer() {
          return Fancybox.isInactive() && window.PYTHON_HAS_EMBEDDED_PLAYER && this.canOpenRandomVideo();
        }

        canFindSimilarVideos() {
          return window.PYTHON_FEATURE_COMPARISON;
        }

        componentDidMount() {
          this.callbackIndex = KEYBOARD_MANAGER.register(this.getActions().onKeyPressed);
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
          if (!state.status) state.status = this.context.status_updated;
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
          const definitions = {};

          for (let propType of info.prop_types) {
            definitions[propType.name] = propType;
          }

          state.definitions = definitions;
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
            title: this.context.form_title_move_file.format({
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
                if (status === "Cancelled") this.updateStatus(this.context.status_video_not_moved);else this.updateStatus(this.context.status_video_moved.format({
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
            status: this.context.status_ready
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
            prop_types: this.state.prop_types,
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
                status: this.context.status_prop_val_edited.format({
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
          const name = this.state.database.name;
          Fancybox.load( /*#__PURE__*/React.createElement(GenericFormRename, {
            title: this.context.form_title_rename_database.format({
              name
            }),
            header: this.context.text_rename_database,
            description: name,
            data: name,
            onClose: name => {
              this.backend(["rename_database", name], {
                pageNumber: 0
              });
            }
          }));
        }

        deleteDatabase() {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: this.context.dialog_delete_database.format({
              name: this.state.database.name
            }),
            yes: this.context.text_delete,
            action: () => {
              python_call("delete_database").then(databases => this.props.app.dbHome(databases)).catch(backend_error);
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            center: true,
            full: true,
            className: "text-center"
          }, /*#__PURE__*/React.createElement("h1", null, this.context.text_database, " ", /*#__PURE__*/React.createElement("span", {
            className: "red-flag"
          }, this.state.database.name)), this.context.form_content_confirm_delete_database.markdown())));
        }

        confirmAllUniqueMoves() {
          Fancybox.load( /*#__PURE__*/React.createElement(Dialog, {
            title: this.context.action_confirm_all_unique_moves,
            yes: this.context.text_move,
            action: () => {
              python_call("confirm_unique_moves").then(nbMoved => this.updateStatus(`Moved ${nbMoved} video(s)`, true, true)).catch(backend_error);
            }
          }, /*#__PURE__*/React.createElement(Cell, {
            center: true,
            full: true,
            className: "text-center"
          }, this.context.form_content_confirm_unique_moves.markdown())));
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
            APP_STATE.videoHistory.add(filename);
            this.updateStatus(this.context.status_randomly_opened.format({
              path: filename
            }), true, true);
          }).catch(backend_error);
        }

        playlist() {
          python_call("playlist").then(filename => this.updateStatus(`Opened playlist: ${filename}`)).catch(backend_error);
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
            prop_types: this.getStringSetProperties(this.state.prop_types),
            onClose: state => {
              python_call('fill_property_with_terms', state.field, state.onlyEmpty).then(() => this.backend(null, {
                status: this.context.status_filled_property_with_keywords.format({
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
            definitions: this.state.definitions,
            name: name,
            values: values,
            onClose: operation => {
              switch (operation.form) {
                case 'delete':
                  this.backend(['delete_property_value', name, values], {
                    groupSelection: new Set(),
                    status: this.context.status_prop_vals_deleted.format({
                      name: name,
                      values: values.join('", "')
                    })
                  });
                  break;

                case 'edit':
                  this.backend(['edit_property_value', name, values, operation.value], {
                    groupSelection: new Set(),
                    status: this.context.status_prop_vals_edited.format({
                      name: name,
                      values: values.join('", "'),
                      destination: operation.value
                    })
                  });
                  break;

                case 'move':
                  this.backend(['move_property_value', name, values, operation.move], {
                    groupSelection: new Set(),
                    status: this.context.status_prop_val_moved.format({
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

        propToLowercase(def) {
          this.backend(["prop_to_lowercase", def.name]);
        }

        propToUppercase(def) {
          this.backend(["prop_to_uppercase", def.name]);
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

      VideosPage.contextType = LangContext;
    }
  };
});