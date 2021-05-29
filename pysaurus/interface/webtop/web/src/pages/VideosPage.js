import {PAGE_SIZES, SEARCH_TYPE_TITLE, SOURCE_TREE} from "../utils/constants.js";
import {MenuPack} from "../components/MenuPack.js";
import {Pagination} from "../components/Pagination.js";
import {Video} from "../pageComponents/Video.js";
import {FormSourceVideo} from "../forms/FormSourceVideo.js";
import {FormGroup} from "../forms/FormGroup.js";
import {FormSearch} from "../forms/FormSearch.js";
import {FormSort} from "../forms/FormSort.js";
import {GroupView} from "../pageComponents/GroupView.js";
import {FormEditPropertyValue} from "../forms/FormEditPropertyValue.js";
import {FormFillKeywords} from "../forms/FormFillKeywords.js";
import {FormPropertyMultiVideo} from "../forms/FormPropertyMultiVideo.js";
import {Collapsable} from "../components/Collapsable.js";
import {Cross} from "../components/Cross.js";
import {SettingIcon} from "../components/SettingIcon.js";
import {MenuItem} from "../components/MenuItem.js";
import {MenuItemCheck} from "../components/MenuItemCheck.js";
import {MenuItemRadio} from "../components/MenuItemRadio.js";
import {Menu} from "../components/Menu.js";

class Shortcut {
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
        return (
            this.key === event.key.toLowerCase()
            && this.ctrl === event.ctrlKey
            && this.alt === event.altKey
            && this.shift === event.shiftKey
        );
    }
}

class Action {
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
        return <MenuItem shortcut={this.shortcut.str} action={this.callback}>{title || this.title}</MenuItem>;
    }

    toSettingIcon(title = undefined) {
        return <SettingIcon title={`${title || this.title} (${this.shortcut.str})`} action={this.callback}/>;
    }

    toCross(title = undefined) {
        return <Cross title={`${title || this.title} (${this.shortcut.str})`} action={this.callback}/>;
    }
}

class Actions {
    /**
     * @param actions {Object.<string, Action>}
     */
    constructor(actions) {
        /** @type {Object.<string, Action>} */
        this.actions = actions;

        const shortcutToName = {};
        for (let name of Object.keys(actions)) {
            const shortcut = actions[name].shortcut.str;
            if (shortcutToName.hasOwnProperty(shortcut))
                throw new Error(`Duplicated shortcut ${shortcut} for ${shortcutToName[shortcut]} and ${name}`);
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
}

class Filter extends React.Component {
    constructor(props) {
        // page: VideosPage
        super(props);
    }

    static compareSources(sources1, sources2) {
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
                        <div>{features.actions.select.toSettingIcon()}</div>
                        {!Filter.compareSources(window.PYTHON_DEFAULT_SOURCES, sources) ?
                            <div>{features.actions.unselect.toCross()}</div> : ''}
                    </td>
                </tr>
                <tr>
                    <td>
                        {groupDef ? (
                            <div>Grouped</div>
                        ) : <div className="no-filter">Ungrouped</div>}
                    </td>
                    <td>
                        <div>{features.actions.group.toSettingIcon(groupDef ? 'Edit ...' : 'Group ...')}</div>
                        {groupDef ? <div>{features.actions.ungroup.toCross()}</div> : ''}
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
                        <div>{features.actions.search.toSettingIcon(searchDef ? 'Edit ...' : 'Search ...')}</div>
                        {searchDef ? <div>{features.actions.unsearch.toCross()}</div> : ''}
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
                        <div>{features.actions.sort.toSettingIcon()}</div>
                        {sortingIsDefault ? '' : <div>{features.actions.unsort.toCross()}</div>}
                    </td>
                </tr>
                <tr>
                    <td>
                        {selectionSize ? (
                            <div>
                                <div>Selected</div>
                                <div>{selectedAll ? 'all' : ''} {selectionSize} {selectedAll ? '' : `/ ${backend.nbVideos}`} video{selectionSize < 2 ? '' : 's'}</div>
                                <div className="mb-1">
                                    <button onClick={app.displayOnlySelected}>
                                        {backend.displayOnlySelected ?
                                            'Display all videos' :
                                            'Display only selected videos'}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div>No videos selected</div>
                        )}
                        {selectedAll ? '' : <div className="mb-1">
                            <button onClick={app.selectAll}>select all</button>
                        </div>}
                        {selectionSize ? (
                            <div className="mb-1">
                                <MenuPack title="Edit property ...">
                                    {backend.properties.map((def, index) => (
                                        <MenuItem key={index}
                                                  action={() => app.editPropertiesForManyVideos(def.name)}>{def.name}</MenuItem>
                                    ))}
                                </MenuPack>
                            </div>
                        ) : ''}
                    </td>
                    <td>
                        {selectionSize ? <Cross title={`Deselect all`} action={app.deselect}/> : ''}
                    </td>
                </tr>
                </tbody>
            </table>
        );
    }
}

export class VideosPage extends React.Component {
    constructor(props) {
        // parameters: {backend state}
        // app: App
        super(props);
        this.state = Object.assign({
            status: 'Loaded.',
            confirmDeletion: true,
            path: [],
            selection: new Set(),
            displayOnlySelected: false,
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
            openRandomVideo: new Action("Ctrl+O", "Open random video", this.openRandomVideo),
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

        return (
            <div id="videos">
                <header className="horizontal">
                    <MenuPack title="Options">
                        <Menu title="Filter videos ...">
                            {this.features.actions.select.toMenuItem()}
                            {this.features.actions.group.toMenuItem()}
                            {this.features.actions.search.toMenuItem()}
                            {this.features.actions.sort.toMenuItem()}
                        </Menu>
                        {notFound || !nbVideos ? '' : this.features.actions.openRandomVideo.toMenuItem()}
                        {this.features.actions.reload.toMenuItem()}
                        {this.features.actions.manageProperties.toMenuItem()}
                        {stringSetProperties.length ?
                            <MenuItem action={this.fillWithKeywords}>Put keywords into a property ...</MenuItem> : ''}
                        <Menu title="Page size ...">
                            {PAGE_SIZES.map((count, index) => (
                                <MenuItemRadio key={index}
                                               checked={this.state.pageSize === count}
                                               value={count}
                                               action={this.setPageSize}>
                                    {count} video{count > 1 ? 's' : ''} per page
                                </MenuItemRadio>
                            ))}
                        </Menu>
                        <MenuItemCheck checked={this.state.confirmDeletion} action={this.confirmDeletionForNotFound}>
                            confirm deletion for entries not found
                        </MenuItemCheck>
                        {this.state.properties.length > 10 ? (
                            <Menu title="Group videos by property ...">{
                                this.state.properties.map((def, index) => (
                                    <MenuItem key={index} action={() => this.backendGroupVideos(`:${def.name}`)}>
                                        {def.name}
                                    </MenuItem>
                                ))
                            }</Menu>
                        ) : (
                            this.state.properties.map((def, index) => (
                                <MenuItem key={index} action={() => this.backendGroupVideos(`:${def.name}`)}>
                                    Group videos by property: {def.name}
                                </MenuItem>
                            ))
                        )}
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
                        <Collapsable lite={false} className="filter" title="Filter">
                            <Filter page={this}/>
                        </Collapsable>
                        {this.state.path.length ? (
                            <Collapsable lite={false} className="filter" title="Classifier path">
                                {stringProperties.length ? (
                                    <div className="path-menu">
                                        <MenuPack title="Concatenate path into ...">
                                            {stringProperties.map((def, i) => (
                                                <MenuItem key={i}
                                                          action={() => this.classifierConcatenate(def.name)}>{def.name}</MenuItem>
                                            ))}
                                            <MenuItem
                                                action={() => this.classifierConcatenate(groupField)}>{groupField}</MenuItem>
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
                            </Collapsable>
                        ) : ''}
                        {groupDef ? (
                            <Collapsable lite={false} className="group" title="Groups">
                                <GroupView
                                    key={`${groupDef.field}-${groupDef.groups.length}-${this.state.path.join('-')}`}
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
                            </Collapsable>
                        ) : ''}
                    </div>
                    <div className="main-panel videos">{this.state.videos.map(data => (
                        <Video key={data.video_id}
                               data={data}
                               index={data.local_id}
                               parent={this}
                               selected={this.state.selection.has(data.video_id)}
                               onSelect={this.onVideoSelection}
                               confirmDeletion={this.state.confirmDeletion}/>
                    ))}</div>
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

    componentDidMount() {
        this.callbackIndex = KEYBOARD_MANAGER.register(this.features.onKeyPressed);
    }

    componentWillUnmount() {
        KEYBOARD_MANAGER.unregister(this.callbackIndex);
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
        const pageSize = state.pageSize !== undefined ? state.pageSize : this.state.pageSize;
        const pageNumber = state.pageNumber !== undefined ? state.pageNumber : this.state.pageNumber;
        const displayOnlySelected = state.displayOnlySelected !== undefined ? state.displayOnlySelected : this.state.displayOnlySelected;
        const selection = displayOnlySelected ? Array.from(state.selection !== undefined ? state.selection : this.state.selection) : [];
        python_call('get_info_and_videos', pageSize, pageNumber, selection)
            .then(info => {
                Object.assign(state, info);
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

    unselectVideos() {
        python_call('set_sources', null)
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }

    selectVideos() {
        this.props.app.loadDialog('Select Videos', onClose => (
            <FormSourceVideo tree={SOURCE_TREE} sources={this.state.sources} onClose={sources => {
                onClose();
                if (sources && sources.length) {
                    python_call('set_sources', sources)
                        .then(() => this.updatePage({pageNumber: 0}))
                        .catch(backend_error);
                }
            }}/>
        ));
    }

    groupVideos() {
        const group_def = this.state.groupDef || {field: null, reverse: null};
        this.props.app.loadDialog('Group videos:', onClose => (
            <FormGroup definition={group_def} properties={this.state.properties} onClose={criterion => {
                onClose();
                if (criterion) {
                    python_call('set_groups', criterion.field, criterion.sorting, criterion.reverse, criterion.allowSingletons, criterion.allowMultiple)
                        .then(() => this.updatePage({pageNumber: 0}))
                        .catch(backend_error);
                }
            }}/>
        ));
    }

    backendGroupVideos(field, sorting = "count", reverse = true, allowSingletons = true, allowMultiple = true) {
        python_call('set_groups', field, sorting, reverse, allowSingletons, allowMultiple)
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }

    editPropertiesForManyVideos(propertyName) {
        const videos = Array.from(this.state.selection);
        python_call('count_prop_values', propertyName, videos)
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
            }}/>
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
        python_call('set_groups', '')
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
        if (this.state.notFound || !this.state.nbVideos)
            return;
        python_call('open_random_video')
            .then(filename => {
                this.setState({status: `Randomly opened: ${filename}`});
            })
            .catch(backend_error);
    }

    reloadDatabase() {
        this.props.app.loadHomePage(true);
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
            <FormEditPropertyValue properties={this.generatePropTable(this.state.properties)}
                                   name={name}
                                   values={values}
                                   onClose={operation => {
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

    focusPropertyValue(propertyName, propertyValue) {
        python_call('set_groups', `:${propertyName}`, "count", true, true, true)
            .then(() => python_call('classifier_select_group_by_value', propertyValue))
            .then(() => this.updatePage({pageNumber: 0}))
            .catch(backend_error);
    }
}
