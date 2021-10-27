import {FIELD_MAP, PAGE_SIZES, SEARCH_TYPE_TITLE, SOURCE_TREE} from "../utils/constants.js";
import {MenuPack} from "../components/MenuPack.js";
import {Pagination} from "../components/Pagination.js";
import {Video} from "../components/Video.js";
import {FormVideosSource} from "../forms/FormVideosSource.js";
import {FormVideosGrouping} from "../forms/FormVideosGrouping.js";
import {FormVideosSearch} from "../forms/FormVideosSearch.js";
import {FormVideosSort} from "../forms/FormVideosSort.js";
import {GroupView} from "../components/GroupView.js";
import {FormPropertyEditSelectedValues} from "../forms/FormPropertyEditSelectedValues.js";
import {FormVideosKeywordsToProperty} from "../forms/FormVideosKeywordsToProperty.js";
import {FormSelectedVideosEditProperty} from "../forms/FormSelectedVideosEditProperty.js";
import {Collapsable} from "../components/Collapsable.js";
import {Cross} from "../components/Cross.js";
import {MenuItem} from "../components/MenuItem.js";
import {MenuItemCheck} from "../components/MenuItemCheck.js";
import {MenuItemRadio} from "../components/MenuItemRadio.js";
import {Menu} from "../components/Menu.js";
import {Selector} from "../utils/Selector.js";
import {Action} from "../utils/Action.js";
import {Actions} from "../utils/Actions.js";
import {ActionToMenuItem} from "../components/ActionToMenuItem.js";
import {ActionToSettingIcon} from "../components/ActionToSettingIcon.js";
import {ActionToCross} from "../components/ActionToCross.js";
import {backend_error, python_call} from "../utils/backend.js";
import {FancyBox} from "../dialogs/FancyBox.js";
import {HomePage} from "./HomePage.js";
import {FormDatabaseEditFolders} from "../forms/FormDatabaseEditFolders.js";
import {FormDatabaseRename} from "../forms/FormDatabaseRename.js";
import {Dialog} from "../dialogs/Dialog.js";
import {Cell} from "../components/Cell.js";
import {FormNewPredictionProperty} from "../forms/FormNewPredictionProperty.js";

function compareSources(sources1, sources2) {
    if (sources1.length !== sources2.length)
        return false;
    for (let i = 0; i < sources1.length; ++i) {
        const path1 = sources1[i];
        const path2 = sources2[i];
        if (path1.length !== path2.length)
            return false;
        for (let j = 0; j < path1.length; ++j) {
            if (path1[j] !== path2[j])
                return false;
        }
    }
    return true;
}

function arrayEquals(a, b) {
    return Array.isArray(a) &&
        Array.isArray(b) &&
        a.length === b.length &&
        a.every((val, index) => val === b[index]);
}

export class VideosPage extends React.Component {
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
            groupSelection: new Set(),
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
        this.notificationCallbackIndex = -1;
        // 14 shortcuts currently.
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
            nextPage: new Action("Ctrl+ArrowRight", PYTHON_LANG.action_go_to_next_page, this.nextPage, Fancybox.isInactive),
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

        return (
            <div id="videos" className="absolute-plain p-4 vertical">
                <header className="horizontal flex-shrink-0">
                    <MenuPack title={PYTHON_LANG.menu_database}>
                        {<ActionToMenuItem action={actions.reload}/>}
                        <MenuItem action={this.renameDatabase}>
                            {PYTHON_LANG.action_rename_database.format({name: this.state.database.name})}
                        </MenuItem>
                        <MenuItem action={this.editDatabaseFolders}>
                            {PYTHON_LANG.action_edit_database_folders.format({count: this.state.database.folders.length})}
                        </MenuItem>
                        <Menu title={PYTHON_LANG.menu_close_database}>
                            <MenuItem action={this.closeDatabase}>
                                <strong>{PYTHON_LANG.action_close_database}</strong>
                            </MenuItem>
                        </Menu>
                        <MenuItem className="red-flag" action={this.deleteDatabase}>
                            {PYTHON_LANG.action_delete_database}
                        </MenuItem>
                    </MenuPack>
                    <MenuPack title={PYTHON_LANG.menu_videos}>
                        <Menu title={PYTHON_LANG.menu_filter_videos}>
                            {<ActionToMenuItem action={actions.select}/>}
                            {<ActionToMenuItem action={actions.group}/>}
                            {<ActionToMenuItem action={actions.search}/>}
                            {<ActionToMenuItem action={actions.sort}/>}
                        </Menu>
                        {aFilterIsSet ? (
                            <Menu title={PYTHON_LANG.menu_reset_filters}>
                                {this.sourceIsSet() ? <ActionToMenuItem action={actions.unselect}/> : ""}
                                {this.groupIsSet() ? <ActionToMenuItem action={actions.ungroup}/> : ""}
                                {this.searchIsSet() ? <ActionToMenuItem action={actions.unsearch}/> : ""}
                                {this.sortIsSet() ? <ActionToMenuItem action={actions.unsort}/> : ""}
                            </Menu>
                        ) : ""}
                        {this.canOpenRandomVideo() ? <ActionToMenuItem action={actions.openRandomVideo}/> : ""}
                        {this.canOpenRandomPlayer() ? <ActionToMenuItem action={actions.openRandomPlayer}/> : ""}
                        {this.canFindSimilarVideos() ? (
                            <MenuItem action={this.findSimilarVideos}>
                                {PYTHON_LANG.action_search_similar_videos}
                            </MenuItem>
                        ) : ""}
                        {this.canFindSimilarVideos() ? (
                            <Menu title={PYTHON_LANG.menu_search_similar_videos_longer}>
                                <MenuItem action={this.findSimilarVideosIgnoreCache}>
                                    <strong>{PYTHON_LANG.action_ignore_cache}</strong>
                                </MenuItem>
                            </Menu>
                        ) : ""}
                        {groupedByMoves ? (
                            <MenuItem action={this.confirmAllUniqueMoves}>
                                <strong><em>{PYTHON_LANG.action_confirm_all_unique_moves}</em></strong>
                            </MenuItem>
                        ) : ""}
                    </MenuPack>
                    <MenuPack title={PYTHON_LANG.menu_properties}>
                        {<ActionToMenuItem action={actions.manageProperties}/>}
                        {stringSetProperties.length ? <MenuItem
                            action={this.fillWithKeywords}>{PYTHON_LANG.action_put_keywords_into_property}</MenuItem> : ""}
                        {this.state.properties.length > 5 ? (
                            <Menu title={PYTHON_LANG.menu_group_videos_by_property}>{
                                this.state.properties.map((def, index) => (
                                    <MenuItem key={index} action={() => this.backendGroupVideos(def.name, true)}>
                                        {def.name}
                                    </MenuItem>
                                ))
                            }</Menu>
                        ) : (
                            this.state.properties.map((def, index) => (
                                <MenuItem key={index} action={() => this.backendGroupVideos(def.name, true)}>
                                    {PYTHON_LANG.action_group_videos_by_property.format({name: def.name})}
                                </MenuItem>
                            ))
                        )}
                    </MenuPack>
                    <MenuPack title={PYTHON_LANG.menu_predictors}>
                        <MenuItem
                            action={this.createPredictionProperty}>{PYTHON_LANG.action_create_prediction_property}</MenuItem>
                        <MenuItem
                            action={this.populatePredictionProperty}>{PYTHON_LANG.action_populate_prediction_property_manually}</MenuItem>
                        {predictionProperties.length ? (
                            <Menu title={PYTHON_LANG.menu_compute_prediction}>
                                {predictionProperties.map((def, i) => (
                                    <MenuItem key={i}
                                              action={() => this.computePredictionProperty(def.name)}>{def.name}</MenuItem>
                                ))}
                            </Menu>
                        ) : ""}
                        {predictionProperties.length ? (
                            <Menu title={PYTHON_LANG.menu_apply_prediction}>
                                {predictionProperties.map((def, i) => (
                                    <MenuItem key={i}
                                              action={() => this.applyPrediction(def.name)}>{def.name}</MenuItem>
                                ))}
                            </Menu>
                        ) : ""}
                    </MenuPack>
                    <MenuPack title={PYTHON_LANG.menu_navigation}>
                        <Menu title={PYTHON_LANG.menu_navigation_videos}>
                            <ActionToMenuItem action={actions.previousPage}/>
                            <ActionToMenuItem action={actions.nextPage}/>
                        </Menu>
                        {this.groupIsSet() ? (
                            <Menu title={PYTHON_LANG.menu_navigation_groups}>
                                <MenuItem action={this.previousGroup}
                                          shortcut="Ctrl+ArrowUp">{PYTHON_LANG.action_go_to_previous_group}</MenuItem>
                                <MenuItem action={this.nextGroup}
                                          shortcut="Ctrl+ArrowDown">{PYTHON_LANG.action_go_to_next_group}</MenuItem>
                            </Menu>
                        ) : ""}
                    </MenuPack>
                    <MenuPack title={PYTHON_LANG.menu_options}>
                        <Menu title={PYTHON_LANG.menu_page_size}>
                            {PAGE_SIZES.map((count, index) => (
                                <MenuItemRadio key={index}
                                               checked={this.state.pageSize === count}
                                               value={count}
                                               action={this.setPageSize}>
                                    {PYTHON_LANG.action_page_size.format({count})}
                                </MenuItemRadio>
                            ))}
                        </Menu>
                        <MenuItemCheck checked={this.state.confirmDeletion} action={this.confirmDeletionForNotFound}>
                            {PYTHON_LANG.action_confirm_deletion_for_entries_not_found}
                        </MenuItemCheck>
                    </MenuPack>
                    <div className="pagination text-right">
                        <Pagination singular={PYTHON_LANG.word_page}
                                    plural={PYTHON_LANG.word_pages}
                                    nbPages={nbPages}
                                    pageNumber={this.state.pageNumber}
                                    key={this.state.pageNumber}
                                    onChange={this.changePage}/>
                    </div>
                </header>
                <div className="frontier block flex-shrink-0"/>
                <div className="content position-relative flex-grow-1">
                    <div className="absolute-plain horizontal">
                        <div className="side-panel vertical">
                            <Collapsable lite={false} className="filter flex-shrink-0" title={PYTHON_LANG.section_filter}>
                                {this.renderFilter()}
                            </Collapsable>
                            {this.state.path.length ? (
                                <Collapsable lite={false} className="filter flex-shrink-0"
                                             title={PYTHON_LANG.section_classifier_path}>
                                    {stringProperties.length ? (
                                        <div className="path-menu text-center p-2">
                                            <MenuPack title={PYTHON_LANG.menu_concatenate_path}>
                                                {stringProperties.map((def, i) => (
                                                    <MenuItem key={i}
                                                              action={() => this.classifierConcatenate(def.name)}>
                                                        {def.name}
                                                    </MenuItem>
                                                ))}
                                            </MenuPack>
                                            <div className="pt-2">
                                                <button className="block"
                                                        onClick={this.classifierReversePath}>{PYTHON_LANG.action_reverse_path}</button>
                                            </div>
                                        </div>
                                    ) : ""}
                                    {this.state.path.map((value, index) => (
                                        <div key={index} className="path-step horizontal px-2 py-1">
                                            <div className="flex-grow-1">{value.toString()}</div>
                                            {index === this.state.path.length - 1 ? (
                                                <div className="icon">
                                                    <Cross title={PYTHON_LANG.text_unstack} action={this.classifierUnstack}/>
                                                </div>
                                            ) : ""}
                                        </div>
                                    ))}
                                </Collapsable>
                            ) : ""}
                            {groupDef ? (
                                <div className="flex-grow-1 position-relative">
                                    <Collapsable lite={false} className="group absolute-plain vertical"
                                                 title={PYTHON_LANG.section_groups}>
                                        <GroupView
                                            groupDef={groupDef}
                                            isClassified={!!this.state.path.length}
                                            pageSize={this.state.groupPageSize}
                                            pageNumber={this.state.groupPageNumber}
                                            selection={this.state.groupSelection}
                                            onGroupViewState={this.onGroupViewState}
                                            onOptions={this.editPropertyValue}
                                            onPlus={
                                                groupDef.is_property && this.state.definitions[groupDef.field].multiple
                                                    ? this.classifierSelectGroup : null
                                            }/>
                                    </Collapsable>
                                </div>
                            ) : ""}
                        </div>
                        <div className="main-panel videos overflow-auto">{this.state.videos.map(data => (
                            <Video key={data.video_id}
                                   data={data}
                                   propDefs={this.state.properties}
                                   groupDef={groupDef}
                                   selected={this.state.selector.has(data.video_id)}
                                   onSelect={this.onVideoSelection}
                                   onMove={this.moveVideo}
                                   onSelectPropertyValue={this.focusPropertyValue}
                                   onInfo={this.updateStatus}
                                   confirmDeletion={this.state.confirmDeletion}
                                   groupedByMoves={groupedByMoves}/>
                        ))}</div>
                    </div>
                </div>
                <footer className="horizontal flex-shrink-0">
                    <div className="footer-status clickable" title={this.state.status} onClick={this.resetStatus}>
                        {this.state.status}
                    </div>
                    <div className="footer-information text-right">
                        {groupDef ? (
                            <div className="info group">
                                {groupDef.groups.length ?
                                    PYTHON_LANG.text_group.format({
                                        group: (groupDef.group_id + 1),
                                        count: groupDef.groups.length
                                    })
                                    : PYTHON_LANG.text_no_group}
                            </div>
                        ) : ""}
                        <div className="info count">{nbVideos} video{nbVideos > 1 ? 's' : ""}</div>
                        <div className="info size">{validSize}</div>
                        <div className="info length">{validLength}</div>
                    </div>
                </footer>
            </div>
        );
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
        return (
            <table className="filter w-100">
                <tbody>
                {/** Sources **/}
                <tr>
                    <td>
                        {sources.map((source, index) => (
                            <div key={index}>{source.join(" ").replace('_', " ")}</div>
                        ))}
                    </td>
                    <td>
                        <div><ActionToSettingIcon action={actions.select}/></div>
                        {!compareSources(window.PYTHON_DEFAULT_SOURCES, sources) ?
                            <div><ActionToCross action={actions.unselect}/></div> : ""}
                    </td>
                </tr>
                {/** Grouping **/}
                <tr>
                    <td>
                        {groupDef ? (
                            <div>{PYTHON_LANG.text_grouped}</div>
                        ) : <div className="no-filter">{PYTHON_LANG.text_ungrouped}</div>}
                    </td>
                    <td>
                        <div>
                            <ActionToSettingIcon action={actions.group}
                                                 title={groupDef ? PYTHON_LANG.action_edit : PYTHON_LANG.action_group}/>
                        </div>
                        {groupDef ? <div><ActionToCross action={actions.ungroup}/></div> : ""}
                    </td>
                </tr>
                {/** Search **/}
                <tr>
                    <td>
                        {searchDef ? (
                            <div>
                                <div>{PYTHON_LANG.text_searched.format({text: SEARCH_TYPE_TITLE[searchDef.cond]})}</div>
                                <div className="word-break-all">&quot;<strong>{searchDef.text}</strong>&quot;</div>
                            </div>
                        ) : <div className="no-filter">{PYTHON_LANG.text_no_search}</div>}
                    </td>
                    <td>
                        <div>
                            <ActionToSettingIcon action={actions.search}
                                                 title={searchDef ? PYTHON_LANG.action_edit : PYTHON_LANG.action_search}/>
                        </div>
                        {searchDef ? <div><ActionToCross action={actions.unsearch}/></div> : ""}
                    </td>
                </tr>
                {/** Sort **/}
                <tr>
                    <td>
                        <div>{PYTHON_LANG.text_sorted_by}</div>
                        {sorting.map((val, i) => (
                            <div key={i}>
                                <strong>{FIELD_MAP.fields[val.substr(1)].title}</strong>{" "}
                                {val[0] === '-' ? (<span>&#9660;</span>) : (<span>&#9650;</span>)}
                            </div>))}
                    </td>
                    <td>
                        <div><ActionToSettingIcon action={actions.sort}/></div>
                        {sortingIsDefault ? "" : <div><ActionToCross action={actions.unsort}/></div>}
                    </td>
                </tr>
                {/** Selection **/}
                <tr>
                    <td>
                        {selectionSize ? (
                            <div>
                                <div>Selected</div>
                                <div>
                                    {selectedAll ?
                                        PYTHON_LANG.text_all_videos_selected.format({count: selectionSize}) :
                                        PYTHON_LANG.text_videos_selected.format({count: selectionSize, total: realNbVideos})}
                                </div>
                                <div className="mb-1">
                                    <button onClick={this.displayOnlySelected}>
                                        {this.state.displayOnlySelected ?
                                            PYTHON_LANG.action_display_all_videos : PYTHON_LANG.action_display_selected_videos}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div>{PYTHON_LANG.text_no_videos_selected}</div>
                        )}
                        {selectedAll ? "" : <div className="mb-1">
                            <button onClick={this.selectAll}>{PYTHON_LANG.action_select_all}</button>
                        </div>}
                        {selectionSize ? (
                            <div className="mb-1">
                                <MenuPack title={PYTHON_LANG.menu_edit_properties}>
                                    {this.state.properties.map((def, index) => (
                                        <MenuItem key={index} action={() => this.editPropertiesForManyVideos(def.name)}>
                                            {def.name}
                                        </MenuItem>
                                    ))}
                                </MenuPack>
                            </div>
                        ) : ""}
                    </td>
                    <td>
                        {selectionSize ? <Cross title={PYTHON_LANG.action_deselect_all} action={this.deselect}/> : ""}
                    </td>
                </tr>
                </tbody>
            </table>
        );
    }

    createPredictionProperty() {
        Fancybox.load(
            <FormNewPredictionProperty onClose={name => {
                this.backend(["create_prediction_property", name]);
            }}/>
        )
    }

    populatePredictionProperty() {
        Fancybox.load(
            <FancyBox title={PYTHON_LANG.form_title_populate_predictor_manually}>
                {PYTHON_LANG.form_content_populate_predictor_manually.markdown()}
            </FancyBox>
        );
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
        if (!state.status)
            state.status = PYTHON_LANG.status_updated;
        python_call("backend", callargs, pageSize, pageNumber, selector)
            .then(info => this.setState(this.parametersToState(state, info), top ? this.scrollTop : undefined))
            .catch(backend_error);
    }

    parametersToState(state, info) {
        if (info.groupDef) {
            const groupPageSize = state.groupPageSize !== undefined ? state.groupPageSize : this.state.groupPageSize;
            const groupPageNumber = state.groupPageNumber !== undefined ? state.groupPageNumber : this.state.groupPageNumber;
            const count = info.groupDef.groups.length;
            const nbPages = Math.floor(count / groupPageSize) + (count % groupPageSize ? 1 : 0);
            state.groupPageNumber = Math.min(Math.max(0, groupPageNumber), nbPages - 1);
        }
        if (info.viewChanged && !state.selector)
            state.selector = new Selector();
        return Object.assign(state, info);
    }

    notify(notification) {
        if (notification.name === "NextRandomVideo")
            this.backend(null, {});
    }

    onGroupViewState(groupState) {
        const state = {};
        if (groupState.hasOwnProperty("pageSize"))
            state.groupPageSize = groupState.pageSize;
        if (groupState.hasOwnProperty("pageNumber"))
            state.groupPageNumber = groupState.pageNumber;
        if (groupState.hasOwnProperty("selection"))
            state.groupSelection = groupState.selection;
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
            this.setState({selector});
        } else {
            selector.remove(videoID);
            if (this.state.displayOnlySelected)
                this.backend(null, {
                    selector,
                    displayOnlySelected: this.state.displayOnlySelected && selector.size(this.state.realNbVideos)
                });
            else
                this.setState({selector});
        }
    }

    moveVideo(videoID, directory) {
        Fancybox.load(
            <FancyBox title={PYTHON_LANG.form_title_move_file.format({path: directory})} onClose={() => {
                python_call("cancel_copy");
            }}>
                <div className="absolute-plain vertical">
                    <HomePage key={window.APP_STATE.idGenerator.next()}
                              app={this.props.app}
                              parameters={{
                                  command: ["move_video_file", videoID, directory],
                                  onReady: (status) => {
                                      Fancybox.close();
                                      if (status === "Cancelled")
                                          this.updateStatus(PYTHON_LANG.status_video_not_moved);
                                      else
                                          this.updateStatus(PYTHON_LANG.status_video_moved.format({directory}), true);
                                  }
                              }}/>
                </div>
            </FancyBox>
        )
    }

    deselect() {
        const selector = this.state.selector.clone();
        selector.clear();
        if (this.state.displayOnlySelected)
            this.backend(null, {selector, displayOnlySelected: false});
        else
            this.setState({selector});
    }

    selectAll() {
        // Should not be called if displayOnlySelected is true.
        const selector = this.state.selector.clone();
        selector.fill();
        if (this.state.displayOnlySelected)
            this.backend(null, {selector});
        else
            this.setState({selector});
    }

    displayOnlySelected() {
        this.backend(null, {displayOnlySelected: !this.state.displayOnlySelected});
    }

    updateStatus(status, reload = false, top = false) {
        if (reload)
            this.backend(null, {status}, top);
        else
            this.setState({status});
    }

    resetStatus() {
        this.setState({status: PYTHON_LANG.status_ready});
    }

    unselectVideos() {
        this.backend(['set_sources', null], {pageNumber: 0});
    }

    selectVideos() {
        Fancybox.load(
            <FormVideosSource tree={SOURCE_TREE} sources={this.state.sources} onClose={sources => {
                this.backend(['set_sources', sources], {pageNumber: 0});
            }}/>
        )
    }

    groupVideos() {
        const groupDef = this.state.groupDef || {field: null, is_property: null, reverse: null};
        Fancybox.load(
            <FormVideosGrouping groupDef={groupDef}
                                properties={this.state.properties}
                                propertyMap={this.state.definitions}
                                onClose={criterion => {
                                    this.backend(['set_groups', criterion.field, criterion.isProperty, criterion.sorting, criterion.reverse, criterion.allowSingletons], {pageNumber: 0});
                                }}/>
        )
    }

    backendGroupVideos(field, isProperty = false, sorting = "count", reverse = true, allowSingletons = true) {
        this.backend(['set_groups', field, isProperty, sorting, reverse, allowSingletons], {pageNumber: 0});
    }

    editPropertiesForManyVideos(propertyName) {
        const selectionSize = this.state.selector.size(this.state.realNbVideos);
        const videoIndices = this.state.selector.toJSON();
        python_call('count_prop_values', propertyName, videoIndices)
            .then(valuesAndCounts => Fancybox.load(
                    <FormSelectedVideosEditProperty nbVideos={selectionSize}
                                                    definition={this.state.definitions[propertyName]}
                                                    values={valuesAndCounts}
                                                    onClose={edition => {
                                                        this.backend(
                                                            ['edit_property_for_videos', propertyName, videoIndices, edition.add, edition.remove],
                                                            {
                                                                pageNumber: 0,
                                                                status: PYTHON_LANG.status_prop_val_edited.format({
                                                                    property: propertyName,
                                                                    count: selectionSize
                                                                })
                                                            }
                                                        );
                                                    }}/>
                )
            )
            .catch(backend_error);
    }

    searchVideos() {
        const search_def = this.state.searchDef || {text: null, cond: null};
        Fancybox.load(
            <FormVideosSearch text={search_def.text} cond={search_def.cond} onClose={criterion => {
                this.backend(['set_search', criterion.text, criterion.cond], {pageNumber: 0});
            }}/>
        )
    }

    sortVideos() {
        Fancybox.load(
            <FormVideosSort sorting={this.state.sorting} onClose={sorting => {
                this.backend(['set_sorting', sorting], {pageNumber: 0});
            }}/>
        )
    }

    editDatabaseFolders() {
        Fancybox.load(
            <FormDatabaseEditFolders database={this.state.database} onClose={paths => {
                python_call("set_video_folders", paths)
                    .then(() => this.props.app.dbUpdate("update_database"))
                    .catch(backend_error);
            }}/>
        )
    }

    renameDatabase() {
        Fancybox.load(
            <FormDatabaseRename title={this.state.database.name} onClose={name => {
                this.backend(["rename_database", name], {pageNumber: 0});
            }}/>
        )
    }

    deleteDatabase() {
        Fancybox.load(
            <Dialog title={PYTHON_LANG.dialog_delete_database.format({name: this.state.database.name})}
                    yes={PYTHON_LANG.text_delete} action={() => {
                python_call("delete_database")
                    .then(databases => this.props.app.dbHome(databases))
                    .catch(backend_error);
            }}>
                <Cell center={true} full={true} className="text-center">
                    <h1>{PYTHON_LANG.text_database} <span className="red-flag">{this.state.database.name}</span></h1>
                    {PYTHON_LANG.form_content_confirm_delete_database.markdown()}
                </Cell>
            </Dialog>
        )
    }

    confirmAllUniqueMoves() {
        Fancybox.load(
            <Dialog title={PYTHON_LANG.action_confirm_all_unique_moves} yes={PYTHON_LANG.text_move} action={() => {
                python_call("confirm_unique_moves")
                    .then(nbMoved => this.updateStatus(`Moved ${nbMoved} video(s)`, true, true))
                    .catch(backend_error);
            }}>
                <Cell center={true} full={true} className="text-center">
                    {PYTHON_LANG.form_content_confirm_unique_moves.markdown()}
                </Cell>
            </Dialog>
        );
    }

    resetGroup() {
        this.backend(['set_groups', ""], {pageNumber: 0});
    }

    resetSearch() {
        this.backend(['set_search', null, null], {pageNumber: 0});
    }

    resetSort() {
        this.backend(['set_sorting', null], {pageNumber: 0});
    }

    openRandomVideo() {
        python_call('open_random_video')
            .then(filename => {
                this.updateStatus(PYTHON_LANG.status_randomly_opened.format({path: filename}), true, true);
            })
            .catch(backend_error);
    }

    openRandomPlayer() {
        python_call('open_random_player')
            .then(() => this.updateStatus("Random player opened!", true, true))
            .catch(backend_error);
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
        Fancybox.load(
            <FormVideosKeywordsToProperty properties={this.getStringSetProperties(this.state.properties)}
                                          onClose={state => {
                                              python_call('fill_property_with_terms', state.field, state.onlyEmpty)
                                                  .then(() => this.backend(null, {status: PYTHON_LANG.status_filled_property_with_keywords.format({name: state.field})}))
                                                  .catch(backend_error);
                                          }}/>
        )
    }

    setPageSize(count) {
        if (count !== this.state.pageSize)
            this.backend(null, {pageSize: count, pageNumber: 0});
    }

    confirmDeletionForNotFound(checked) {
        this.setState({confirmDeletion: checked});
    }

    changeGroup(groupNumber) {
        this.backend(['set_group', groupNumber], {pageNumber: 0});
    }

    selectGroup(value) {
        if (value === -1)
            this.resetGroup();
        else
            this.changeGroup(value);
    }

    changePage(pageNumber) {
        this.backend(null, {pageNumber});
    }

    previousPage() {
        const pageNumber = this.state.pageNumber - 1;
        if (pageNumber >= 0)
            this.changePage(pageNumber);
    }

    nextPage() {
        const pageNumber = this.state.pageNumber + 1;
        if (pageNumber < this.state.nbPages)
            this.changePage(pageNumber);
    }

    previousGroup() {
        const groupID = this.state.groupDef.group_id;
        if (groupID > 0)
            this.onGroupViewState({groupID: groupID - 1});
    }

    nextGroup() {
        const groupID = this.state.groupDef.group_id;
        if (groupID < this.state.groupDef.groups.length - 1)
            this.onGroupViewState({groupID: groupID + 1});
    }

    getStringSetProperties(definitions) {
        return definitions.filter(def => def.multiple && def.type === "str");
    }

    getStringProperties(definitions) {
        return definitions.filter(def => def.type === "str");
    }

    getPredictionProperties(definitions) {
        return definitions.filter(def => (
            def.name.indexOf("<?") === 0
            && def.name.indexOf(">") === def.name.length - 1
            && def.type === "int"
            && def.defaultValue === -1
            && !def.multiple
            && arrayEquals(def.enumeration, [-1, 0, 1])
        ));
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
        for (let index of indices)
            values.push(groupDef.groups[index].value);
        Fancybox.load(
            <FormPropertyEditSelectedValues properties={this.state.definitions}
                                            name={name}
                                            values={values}
                                            onClose={operation => {
                                                switch (operation.form) {
                                                    case 'delete':
                                                        this.backend(
                                                            ['delete_property_value', name, values],
                                                            {
                                                                groupSelection: new Set(),
                                                                status: PYTHON_LANG.status_prop_vals_deleted.format({name: name, values: values.join('", "')})
                                                            }
                                                        );
                                                        break;
                                                    case 'edit':
                                                        this.backend(
                                                            ['edit_property_value', name, values, operation.value],
                                                            {
                                                                groupSelection: new Set(),
                                                                status: PYTHON_LANG.status_prop_vals_edited.format({
                                                                        name: name,
                                                                        values: values.join('", "'),
                                                                        destination: operation.value
                                                                    })
                                                            }
                                                        );
                                                        break;
                                                    case 'move':
                                                        this.backend(
                                                            ['move_property_value', name, values, operation.move],
                                                            {
                                                                groupSelection: new Set(),
                                                                status: PYTHON_LANG.status_prop_val_moved.format({
                                                                    values: values.join('", "'),
                                                                    name: name,
                                                                    destination: operation.move,
                                                                })
                                                            }
                                                        );
                                                        break;
                                                }
                                            }}/>
        )
    }

    classifierReversePath() {
        python_call('classifier_reverse')
            .then(path => this.setState({path}))
            .catch(backend_error);
    }

    classifierSelectGroup(index) {
        this.backend(['classifier_select_group', index], {pageNumber: 0});
    }

    classifierUnstack() {
        this.backend(['classifier_back'], {pageNumber: 0});
    }

    classifierConcatenate(outputPropertyName) {
        this.backend(['classifier_concatenate_path', outputPropertyName], {pageNumber: 0});
    }

    focusPropertyValue(propertyName, propertyValue) {
        this.backend(['classifier_focus_prop_val', propertyName, propertyValue], {pageNumber: 0});
    }

    closeDatabase() {
        python_call("close_database")
            .then(databases => this.props.app.dbHome(databases))
            .catch(backend_error);
    }
}
