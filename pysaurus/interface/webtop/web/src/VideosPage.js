import {SettingIcon, Cross} from "./buttons.js";
import {PAGE_SIZES, FIELDS, SEARCH_TYPE_TITLE} from "./constants.js";
import {MenuPack, MenuItem, Menu, MenuItemCheck} from "./MenuPack.js";
import {Pagination} from "./Pagination.js";
import {Video} from "./Video.js";
import {FormSourceVideo} from "./FormSourceVideo.js";
import {FormGroup} from "./FormGroup.js";
import {FormSearch} from "./FormSearch.js";
import {FormSort} from "./FormSort.js";
import {GroupView} from "./GroupView.js";
import {FormEditPropertyValue} from "./FormEditPropertyValue.js";
import {FormFillKeywords} from "./FormFillKeywords.js";
import {FormPropertyMultiVideo} from "./FormPropertyMultiVideo.js";
import {Stackable} from "./Stackable.js";

const INITIAL_SOURCES = [];
const SHORTCUTS = {
    select: "Ctrl+T",
    group: "Ctrl+G",
    search: "Ctrl+F",
    sort: "Ctrl+S",
    unselect: "Ctrl+Shift+T",
    ungroup: "Ctrl+Shift+G",
    unsearch: "Ctrl+Shift+F",
    unsort: "Ctrl+Shift+S",
    reload: "Ctrl+R",
    manageProperties: "Ctrl+P",
    openRandomVideo: "Ctrl+O",
};
const SPECIAL_KEYS = {
    ctrl: "ctrlKey",
    alt: "altKey",
    shift: "shiftKey",
    maj: "shiftKey",
}

function compareSources(s1, s2) {
    if (s1.length !== s2.length)
        return false;
    for (let i = 0; i < s1.length; ++i) {
        const l1 = s1[i];
        const l2 = s2[i];
        if (l1.length !== l2.length)
            return false;
        for (let j = 0; j < l1.length; ++j) {
            if (l1[j] !== l2[j])
                return false;
        }
    }
    return true;
}

function assertUniqueShortcuts() {
    const duplicates = {};
    for (let key of Object.keys(SHORTCUTS)) {
        const value = SHORTCUTS[key];
        if (duplicates.hasOwnProperty(value))
            throw new Error(`Duplicated shortcut ${value} for ${duplicates[value]} and ${key}.`);
        duplicates[value] = key;
    }
}
assertUniqueShortcuts();

/**
 * @param event {KeyboardEvent}
 * @param shortcut {string}
 */
function shortcutPressed(event, shortcut) {
    const pieces = shortcut.split('+');
    if (!pieces.length)
        return false;
    if (event.key.toLowerCase() !== pieces[pieces.length - 1].toLowerCase())
        return false;
    const specialKeys = new Set();
    for (let i = 0; i < pieces.length - 1; ++i) {
        const key = pieces[i].toLowerCase();
        console.log(`key ${key} has ${SPECIAL_KEYS.hasOwnProperty(key)} event ${event[SPECIAL_KEYS[key]]}`);
        if (!SPECIAL_KEYS.hasOwnProperty(key) || !event[SPECIAL_KEYS[key]])
            return false;
        specialKeys.add(SPECIAL_KEYS[key]);
    }
    for (let key of Object.keys(SPECIAL_KEYS)) {
        if (!specialKeys.has(SPECIAL_KEYS[key]) && event[SPECIAL_KEYS[key]])
            return false;
    }
    console.log(pieces);
    return true;
}

class Filter extends React.Component {
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
        const selectionSize = backend.selection.size;
        const selectedAll = backend.realNbVideos === selectionSize;
        return (
            <table className="filter">
                <tbody>
                <tr>
                    <td>
                        {sources.map((source, index) => (
                            <div key={index}>
                                {source.join(' ').replace('_', ' ')}
                            </div>
                        ))}
                    </td>
                    <td>
                        <div><SettingIcon title={`Select sources ... (${SHORTCUTS.select})`} action={app.selectVideos}/></div>
                        {INITIAL_SOURCES.length && !compareSources(INITIAL_SOURCES[0], sources) ? (
                            <div><Cross title={`Reset selection (${SHORTCUTS.unselect})`} action={app.unselectVideos}/></div>
                        ) : ''}
                    </td>
                </tr>
                <tr>
                    <td>
                        {groupDef ? (
                            <div>Grouped</div>
                        ) : <div className="no-filter">Ungrouped</div>}
                    </td>
                    <td>
                        <div><SettingIcon title={(groupDef ? 'Edit ...' : 'Group ...') + ` (${SHORTCUTS.group})`} action={app.groupVideos}/></div>
                        {groupDef ? <div><Cross title={`Reset group (${SHORTCUTS.ungroup})`} action={app.resetGroup}/></div> : ''}
                    </td>
                </tr>
                <tr>
                    <td>
                        {searchDef ? (
                            <div>
                                <div>Searched {SEARCH_TYPE_TITLE[searchDef.cond]}</div>
                                <div>&quot;<strong>{searchDef.text}</strong>&quot;</div>
                            </div>
                        ) : <div className="no-filter">No search</div>}
                    </td>
                    <td>
                        <div>
                            <SettingIcon title={(searchDef ? 'Edit ...' : 'Search ...') + ` (${SHORTCUTS.search})`} action={app.searchVideos}/>
                        </div>
                        {searchDef ? <div><Cross title={`reset search (${SHORTCUTS.unsearch})`} action={app.resetSearch}/></div> : ''}
                    </td>
                </tr>
                <tr>
                    <td>
                        <div>Sorted by</div>
                        {sorting.map((val, i) => (
                            <div key={i}>
                                <strong>{val.substr(1)}</strong>{' '}
                                {val[0] === '-' ? (<span>&#9660;</span>) : (<span>&#9650;</span>)}
                            </div>))}
                    </td>
                    <td>
                        <div><SettingIcon title={`Sort ... (${SHORTCUTS.sort})`} action={app.sortVideos}/></div>
                        {sortingIsDefault ? '' : <Cross title={`reset sorting (${SHORTCUTS.unsort})`} action={app.resetSort} />}
                    </td>
                </tr>
                <tr>
                    <td>
                        {selectionSize ? (
                            <div>
                                <div>Selected</div>
                                <div>{selectedAll ? 'all' : ''} {selectionSize} {selectedAll ? '' : `/ ${backend.nbVideos}`} video{selectionSize < 2 ? '' : 's'}</div>
                                <div className="mb-1">
                                    <button onClick={app.displayOnlySelected}>{backend.displayOnlySelected ? 'Display all videos' : 'Display only selected videos'}</button>
                                </div>
                            </div>
                        ) : (
                            <div>No videos selected</div>
                        )}
                        {selectedAll ? '' : <div className="mb-1"><button onClick={app.selectAll}>select all</button></div>}
                        {selectionSize ? (
                            <div className="mb-1">
                                <MenuPack title="Edit property ...">
                                    {backend.properties.map((def, index) => (
                                        <MenuItem key={index} action={() => app.editPropertiesForManyVideos(def.name)}>{def.name}</MenuItem>
                                    ))}
                                </MenuPack>
                            </div>
                        ) : ''}
                    </td>
                    <td>
                        {selectionSize ? <Cross title={`Deselect all`} action={app.deselect} /> : ''}
                    </td>
                </tr>
                </tbody>
            </table>
        );
    }
}

export class VideosPage extends React.Component {
    constructor(props) {
        // parameters: {pageSize, pageNumber, info}
        // app: App
        super(props);
        this.state = {
            status: 'Loaded.',
            confirmDeletion: true,
            path: [],
            selection: new Set(),
            displayOnlySelected: false,
        };
        this.changeGroup = this.changeGroup.bind(this);
        this.changePage = this.changePage.bind(this);
        this.checkShortcut = this.checkShortcut.bind(this);
        this.classifierConcatenate = this.classifierConcatenate.bind(this);
        this.classifierSelectGroup = this.classifierSelectGroup.bind(this);
        this.classifierUnstack = this.classifierUnstack.bind(this);
        this.confirmDeletionForNotFound = this.confirmDeletionForNotFound.bind(this);
        this.deselect = this.deselect.bind(this);
        this.displayOnlySelected = this.displayOnlySelected.bind(this);
        this.editPropertiesForManyVideos = this.editPropertiesForManyVideos.bind(this);
        this.editPropertyValue = this.editPropertyValue.bind(this);
        this.fillWithKeywords = this.fillWithKeywords.bind(this);
        this.groupVideos = this.groupVideos.bind(this);
        this.manageProperties = this.manageProperties.bind(this);
        this.onVideoSelection = this.onVideoSelection.bind(this);
        this.openRandomVideo = this.openRandomVideo.bind(this);
        this.parametersToState = this.parametersToState.bind(this);
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
        this.updatePage = this.updatePage.bind(this);
        this.updateStatus = this.updateStatus.bind(this);
        this.reverseClassifierPath = this.reverseClassifierPath.bind(this);

        this.parametersToState(this.props.parameters, this.state);
        this.callbackIndex = -1;
        this.shortcuts = {
            [SHORTCUTS.select]: this.selectVideos,
            [SHORTCUTS.group]: this.groupVideos,
            [SHORTCUTS.search]: this.searchVideos,
            [SHORTCUTS.unselect]: this.unselectVideos,
            [SHORTCUTS.ungroup]: this.resetGroup,
            [SHORTCUTS.unsearch]: this.resetSearch,
            [SHORTCUTS.unsort]: this.resetSort,
            [SHORTCUTS.sort]: this.sortVideos,
            [SHORTCUTS.reload]: this.reloadDatabase,
            [SHORTCUTS.manageProperties]: this.manageProperties,
            [SHORTCUTS.openRandomVideo]: this.openRandomVideo,
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
        const stringProperties = this.getStringProperties(this.state.properties);
        const groupField = groupDef && groupDef.field.charAt(0) === ':' ? groupDef.field.substr(1) : null;

        return (
            <div id="videos">
                <header className="horizontal">
                    <MenuPack title="Options">
                        <Menu title="Filter videos ...">
                            <MenuItem shortcut={SHORTCUTS.select} action={this.selectVideos}>Select videos ...</MenuItem>
                            <MenuItem shortcut={SHORTCUTS.group} action={this.groupVideos}>Group ...</MenuItem>
                            <MenuItem shortcut={SHORTCUTS.search} action={this.searchVideos}>Search ...</MenuItem>
                            <MenuItem shortcut={SHORTCUTS.sort} action={this.sortVideos}>Sort ...</MenuItem>
                        </Menu>
                        {notFound || !nbVideos ? '' : <MenuItem shortcut={SHORTCUTS.openRandomVideo} action={this.openRandomVideo}>Open random video</MenuItem>}
                        <MenuItem shortcut={SHORTCUTS.reload} action={this.reloadDatabase}>Reload database ...</MenuItem>
                        <MenuItem shortcut={SHORTCUTS.manageProperties} action={this.manageProperties}>Manage properties ...</MenuItem>
                        {stringSetProperties.length ? <MenuItem action={this.fillWithKeywords}>Put keywords into a property ...</MenuItem> : ''}
                        <Menu title="Page size ...">
                            {PAGE_SIZES.map((count, index) => (
                                <MenuItemCheck key={index}
                                               checked={this.state.pageSize === count}
                                               action={checked => {if (checked) this.setPageSize(count);}}>
                                    {count} video{count > 1 ? 's' : ''} per page
                                </MenuItemCheck>
                            ))}
                        </Menu>
                        <MenuItemCheck checked={this.state.confirmDeletion} action={this.confirmDeletionForNotFound}>
                            confirm deletion for entries not found
                        </MenuItemCheck>
                    </MenuPack>
                    <div className="buttons"/>
                    <div className="pagination">
                        <Pagination singular="page"
                                    plural="pages"
                                    nbPages={nbPages}
                                    pageNumber={this.state.pageNumber}
                                    key={this.state.pageNumber}
                                    onChange={this.changePage}/>
                    </div>
                </header>
                <div className="frontier"/>
                <div className="content">
                    <div className="side-panel">
                        <Stackable className="filter" title="Filter">
                            <Filter page={this} />
                        </Stackable>
                        {this.state.path.length ? (
                            <Stackable className="filter" title="Classifier path">
                                {this.state.path.length > 1 && stringProperties.length ? (
                                    <div className="path-menu">
                                        <MenuPack title="Concatenate path into ...">
                                            {stringProperties.map((def, i) => (
                                                <MenuItem key={i} action={() => this.classifierConcatenate(def.name)}>{def.name}</MenuItem>
                                            ))}
                                            <MenuItem action={() => this.classifierConcatenate(groupField)}>{groupField}</MenuItem>
                                        </MenuPack>
                                        <p>
                                            <button onClick={this.reverseClassifierPath}>reverse path</button>
                                        </p>
                                    </div>
                                ) : ''}
                                {this.state.path.map((value, index) => (
                                    <div key={index} className="path-step horizontal">
                                        <div className="title">{value.toString()}</div>
                                        {index === this.state.path.length - 1 ? (
                                            <div className="icon">
                                                <Cross title="unstack" action={this.classifierUnstack}/>
                                            </div>
                                        ) : ''}
                                    </div>
                                ))}
                            </Stackable>
                        ) : ''}
                        {groupDef ? (
                            <Stackable className="group" title="Groups">
                                <GroupView key={`${groupDef.field}-${groupDef.groups.length}-${this.state.path.join('-')}`}
                                           groupID={groupDef.group_id}
                                           field={groupDef.field}
                                           sorting={groupDef.sorting}
                                           reverse={groupDef.reverse}
                                           groups={groupDef.groups}
                                           inPath={this.state.path.length}
                                           onSelect={this.selectGroup}
                                           onOptions={this.editPropertyValue}
                                           onPlus={
                                               groupDef.field[0] === ':'
                                               && this.state.definitions[groupDef.field.substr(1)].multiple
                                                   ? this.classifierSelectGroup
                                                   : null
                                           }/>
                            </Stackable>
                        ) : ''}
                    </div>
                    <div className="main-panel videos">{this.renderVideos()}</div>
                </div>
                <footer className="horizontal">
                    <div className="footer-status" onClick={this.resetStatus}>{this.state.status}</div>
                    <div className="footer-information">
                        {groupDef ? (
                            <div className="info group">
                                Group {groupDef.group_id + 1}/{groupDef.nb_groups}
                            </div>
                        ) : ''}
                        <div className="info count">{nbVideos} video{nbVideos > 1 ? 's' : ''}</div>
                        <div className="info size">{validSize}</div>
                        <div className="info length">{validLength}</div>
                    </div>
                </footer>
            </div>
        );
    }
    renderVideos() {
        return this.state.videos.map(data => (
            <Video key={data.video_id}
                   data={data}
                   index={data.local_id}
                   parent={this}
                   selected={this.state.selection.has(data.video_id)}
                   onSelect={this.onVideoSelection}
                   confirmDeletion={this.state.confirmDeletion}/>
        ));
    }
    componentDidMount() {
        this.callbackIndex = KEYBOARD_MANAGER.register(this.checkShortcut);
    }
    parametersToState(parameters, state) {
        state.pageSize = parameters.pageSize;
        state.pageNumber = parameters.info.pageNumber;
        state.nbVideos = parameters.info.nbVideos;
        state.realNbVideos = parameters.info.realNbVideos;
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
        state.path = parameters.info.path;
        state.definitions = {};
        for (let def of parameters.info.properties) {
            state.definitions[def.name] = def;
        }
        if (!INITIAL_SOURCES.length)
            INITIAL_SOURCES.push(state.sources);
    }
    onVideoSelection(videoID, selected) {
        const selection = new Set(this.state.selection);
        if (selected) {
            selection.add(videoID);
            this.setState({selection});
        } else if (selection.has(videoID)) {
            selection.delete(videoID);
            const displayOnlySelected = this.state.displayOnlySelected && selection.size;
            const state = {selection, displayOnlySelected};
            if (this.state.displayOnlySelected)
                this.updatePage(state);
            else
                this.setState(state);
        }
    }
    deselect() {
        this.setState({selection: new Set(), displayOnlySelected: false});
    }
    selectAll() {
        python_call('get_view_indices')
            .then(indices => this.setState({selection: new Set(indices)}))
            .catch(backend_error);
    }
    displayOnlySelected() {
        this.updatePage({displayOnlySelected: !this.state.displayOnlySelected});
    }

    scrollTop() {
        const videos = document.querySelector('#videos .videos');
        videos.scrollTop = 0;
    }
    updatePage(state, top = true) {
        // todo what if page size is out of page range ?
        const pageSize = state.pageSize !== undefined ? state.pageSize: this.state.pageSize;
        const pageNumber = state.pageNumber !== undefined ? state.pageNumber: this.state.pageNumber;
        const displayOnlySelected = state.displayOnlySelected !== undefined ? state.displayOnlySelected : this.state.displayOnlySelected;
        const selection = displayOnlySelected ? Array.from(state.selection !== undefined ? state.selection : this.state.selection) : [];
        python_call('get_info_and_videos', pageSize, pageNumber, FIELDS, selection)
            .then(info => {
                this.parametersToState({pageSize, info}, state);
                if (top)
                    this.setState(state, this.scrollTop);
                else
                    this.setState(state);
            })
            .catch(backend_error);
    }
    updateStatus(status, reload = false, top = false) {
        if (reload) {
            this.updatePage({status}, top);
        } else {
            this.setState({status});
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
    unselectVideos() {
        python_call('set_sources', INITIAL_SOURCES[0])
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }

    selectVideos() {
        this.props.app.loadDialog('Select Videos', onClose => (
            <FormSourceVideo tree={this.state.sourceTree} sources={this.state.sources} onClose={sources => {
                onClose();
                if (sources && sources.length) {
                    python_call('set_sources', sources)
                        .then(() => this.updatePage({pageNumber: 0}))
                        .catch(backend_error);
                }
            }} />
        ));
    }
    groupVideos() {
        const group_def = this.state.groupDef || {field: null, reverse: null};
        this.props.app.loadDialog('Group videos:', onClose => (
            <FormGroup definition={group_def} properties={this.state.properties} onClose={criterion => {
                onClose();
                if (criterion) {
                    python_call('group_videos', criterion.field, criterion.sorting, criterion.reverse, criterion.allowSingletons, criterion.allowMultiple)
                        .then(() => this.updatePage({pageNumber: 0}))
                        .catch(backend_error);
                }
            }}/>
        ));
    }
    editPropertiesForManyVideos(propertyName) {
        const videos = Array.from(this.state.selection);
        python_call('get_prop_values', propertyName, videos)
            .then(valuesAndCounts => this.props.app.loadDialog(
                    `Edit property "${propertyName}" for ${this.state.selection.size} video${this.state.selection.size < 2 ? '' : 's'}`,
                    onClose => (
                        <FormPropertyMultiVideo nbVideos={this.state.selection.size}
                                                definition={this.state.definitions[propertyName]}
                                                values={valuesAndCounts}
                                                onClose={edition => {
                            onClose();
                            if (edition) {
                                python_call('edit_property_for_videos', propertyName, videos, edition.add, edition.remove)
                                    .then(() => this.updateStatus(`Edited property "${propertyName}" for ${this.state.selection.size} video${this.state.selection.size < 2 ? '' : 's'}`, true))
                                    .catch(backend_error);
                            }
                        }}/>
                    )
                )
            )
            .catch(backend_error);
    }
    searchVideos() {
        const search_def = this.state.searchDef || {text: null, cond: null};
        this.props.app.loadDialog('Search videos', onClose => (
            <FormSearch text={search_def.text} cond={search_def.cond} onClose={criterion => {
                onClose();
                if (criterion && criterion.text.length && criterion.cond.length) {
                    python_call('set_search', criterion.text, criterion.cond)
                        .then(() => this.updatePage({pageNumber: 0}))
                        .catch(backend_error);
                }
            }} />
        ));
    }
    sortVideos() {
        const sorting = this.state.sorting;
        this.props.app.loadDialog('Sort videos', onClose => (
            <FormSort sorting={sorting} onClose={sorting => {
                onClose();
                if (sorting && sorting.length) {
                    python_call('set_sorting', sorting)
                        .then(() => this.updatePage({pageNumber: 0}))
                        .catch(backend_error);
                }
            }}/>
        ));
    }
    resetGroup() {
        python_call('group_videos', '')
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }
    resetSearch() {
        python_call('set_search', null, null)
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }
    resetSort() {
        python_call('set_sorting', [])
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }
    openRandomVideo() {
        python_call('open_random_video')
            .then(filename => {
                this.setState({status: `Randomly opened: ${filename}`});
            })
            .catch(backend_error);
    }
    reloadDatabase() {
        this.props.app.loadPage("home", {update: true});
    }
    manageProperties() {
        this.props.app.loadPropertiesPage();
    }
    fillWithKeywords() {
        this.props.app.loadDialog(`Fill property`, onClose => (
            <FormFillKeywords properties={this.getStringSetProperties(this.state.properties)} onClose={state => {
                onClose();
                if (state) {
                    python_call('fill_property_with_terms', state.field, state.onlyEmpty)
                        .then(() => this.updateStatus(
                            `Filled property "${state.field}" with video keywords.`, true, true))
                        .catch(backend_error);
                }
            }}/>
        ));
    }
    setPageSize(count) {
        if (count !== this.state.pageSize)
            this.updatePage({pageSize: count, pageNumber: 0});
    }
    confirmDeletionForNotFound(checked) {
        this.setState({confirmDeletion: checked});
    }
    changeGroup(groupNumber) {
        python_call('set_group', groupNumber)
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }
    selectGroup(value) {
        if (value === -1)
            this.resetGroup();
        else
            this.changeGroup(value);
    }
    changePage(pageNumber) {
        this.updatePage({pageNumber});
    }
    getStringSetProperties(definitions) {
        const properties = [];
        for (let def of definitions) {
            if (def.multiple && def.type === "str")
                properties.push(def);
        }
        return properties;
    }
    getMultipleProperties(definitions) {
        const properties = [];
        for (let def of definitions) {
            if (def.multiple)
                properties.push(def);
        }
        return properties;
    }
    getStringProperties(definitions) {
        const field = this.state.groupDef ? this.state.groupDef.field : null;
        const properties = [];
        for (let def of definitions) {
            if (def.type === "str" && (!field || field.charAt(0) !== ':' || def.name !== field.substr(1)))
                properties.push(def);
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
    reverseClassifierPath() {
        python_call('classifier_reverse')
            .then(path => this.setState({path}))
            .catch(backend_error);
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
        for (let index of indicesSet.values())
            indices.push(index);
        indices.sort();
        for (let index of indices)
            values.push(groupDef.groups[index].value);
        let title;
        if (values.length === 1)
            title = `Property "${name}", value "${values[0]}"`;
        else
            title = `Property "${name}", ${values.length} values"`;
        this.props.app.loadDialog(title, onClose => (
            <FormEditPropertyValue properties={this.generatePropTable(this.state.properties)} name={name} values={values} onClose={operation => {
                onClose();
                if (operation) {
                    switch (operation.form) {
                        case 'delete':
                            python_call('delete_property_value', name, values)
                                .then(() => this.updateStatus(`Property value deleted: "${name}" / "${values.join('", "')}"`, true))
                                .catch(backend_error)
                            break;
                        case 'edit':
                            python_call('edit_property_value', name, values, operation.value)
                                .then(() => this.updateStatus(`Property value edited: "${name}" : "${values.join('", "')}" -> "${operation.value}"`, true))
                                .catch(backend_error);
                            break;
                        case 'move':
                            python_call('move_property_value', name, values, operation.move)
                                .then(() => this.updateStatus(`Property value moved: "${values.join('", "')}" from "${name}" to "${operation.move}"`, true))
                                .catch(backend_error)
                            break;
                    }
                }
            }}/>
        ));
    }
    classifierSelectGroup(index) {
        python_call('classifier_select_group', index)
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }
    classifierUnstack() {
        python_call('classifier_back')
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }
    classifierConcatenate(outputPropertyName) {
        python_call('classifier_concatenate_path', outputPropertyName)
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }
}
