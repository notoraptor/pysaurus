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
import {Dialog} from "./Dialog.js";
import {Cell} from "./Cell.js";
import {FormEditPropertyValue} from "./FormEditPropertyValue.js";

const SHORTCUTS = {
    select: "Ctrl+T",
    group: "Ctrl+G",
    search: "Ctrl+F",
    sort: "Ctrl+S",
    reload: "Ctrl+R",
    manageProperties: "Ctrl+P",
};
const SPECIAL_KEYS = {
    ctrl: "ctrlKey",
    alt: "altKey",
    shift: "shiftKey",
    maj: "shiftKey",
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
    for (let i = 0; i < pieces.length - 1; ++i) {
        const key = pieces[i].toLowerCase();
        if (!SPECIAL_KEYS.hasOwnProperty(key) || !event[SPECIAL_KEYS[key]])
            return false;
    }
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
                    <td><SettingIcon title={`Select sources ... (${SHORTCUTS.select})`} action={app.selectVideos}/></td>
                </tr>
                <tr>
                    <td>
                        {groupDef ? (
                            <div>Grouped</div>
                        ) : <div className="no-filter">Ungrouped</div>}
                    </td>
                    <td>
                        <div><SettingIcon title={(groupDef ? 'Edit ...' : 'Group ...') + ` (${SHORTCUTS.group})`} action={app.groupVideos}/></div>
                        {groupDef ? <div><Cross title="Reset group" action={app.resetGroup}/></div> : ''}
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
                        {searchDef ? <div><Cross title="reset search" action={app.resetSearch}/></div> : ''}
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
                        {sortingIsDefault ? '' : <Cross title="reset sorting" action={app.resetSort} />}
                    </td>
                </tr>
                </tbody>
            </table>
        );
    }
}

export class VideosPage extends React.Component {
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
    constructor(props) {
        // parameters: {pageSize, pageNumber, info}
        // app: App
        super(props);
        this.state = {
            status: 'Loaded.',
            confirmDeletion: true,
            stackFilter: false,
            stackGroup: false,
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
        this.parametersToState(this.props.parameters, this.state);
        this.callbackIndex = -1;
        this.shortcuts = {
            [SHORTCUTS.select]: this.selectVideos,
            [SHORTCUTS.group]: this.groupVideos,
            [SHORTCUTS.search]: this.searchVideos,
            [SHORTCUTS.sort]: this.sortVideos,
            [SHORTCUTS.reload]: this.reloadDatabase,
            [SHORTCUTS.manageProperties]: this.manageProperties,
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
                        {notFound || !nbVideos ? '' : <MenuItem action={this.openRandomVideo}>Open random video</MenuItem>}
                        <MenuItem shortcut={SHORTCUTS.reload} action={this.reloadDatabase}>Reload database ...</MenuItem>
                        <MenuItem shortcut={SHORTCUTS.manageProperties} action={this.manageProperties}>Manage properties ...</MenuItem>
                        {stringSetProperties.length ? (
                            <Menu title="Put keywords into a property">
                                {stringSetProperties.map((def, i) => (
                                    <MenuItem key={i} action={() => this.fillWithKeywords(def.name)}>{def.name}</MenuItem>
                                ))}
                            </Menu>
                        ) : ''}
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
                        <div className="stack filter">
                            <div className="stack-title" onClick={this.stackFilter}>
                                <div className="title">Filter</div>
                                <div className="icon">{this.state.stackFilter ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}</div>
                            </div>
                            {this.state.stackFilter ? '' : (
                                <div className="stack-content">
                                    <Filter page={this} />
                                </div>
                            )}
                        </div>
                        {groupDef ? (
                            <div className="stack group">
                                <div className="stack-title" onClick={this.stackGroup}>
                                    <div className="title">Groups</div>
                                    <div className="icon">
                                        {this.state.stackGroup ?
                                            Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}
                                    </div>
                                </div>
                                {this.state.stackGroup ? '' : (
                                    <div className="stack-content">
                                        <GroupView definition={groupDef}
                                                   onSelect={this.selectGroup}
                                                   onValueOptions={this.editPropertyValue}/>
                                    </div>
                                )}
                            </div>
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
                   confirmDeletion={this.state.confirmDeletion}/>
        ));
    }
    componentDidMount() {
        this.callbackIndex = KEYBOARD_MANAGER.register(this.checkShortcut);
    }

    scrollTop() {
        const videos = document.querySelector('#videos .videos');
        videos.scrollTop = 0;
    }
    updatePage(state, top = true) {
        // todo what if page size is out or page range ?
        const pageSize = state.pageSize !== undefined ? state.pageSize: this.state.pageSize;
        const pageNumber = state.pageNumber !== undefined ? state.pageNumber: this.state.pageNumber;
        python_call('get_info_and_videos', pageSize, pageNumber, FIELDS)
            .then(info => {
                this.parametersToState({pageSize, pageNumber, info}, state);
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
    stackGroup() {
        this.setState({stackGroup: !this.state.stackGroup});
    }
    stackFilter() {
        this.setState({stackFilter: !this.state.stackFilter});
    }
    getStringSetProperties(definitions) {
        const properties = [];
        for (let def of definitions) {
            if (def.multiple && def.type === "str")
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
    fillWithKeywords(propertyName) {
        this.props.app.loadDialog(`Fill property "${propertyName}"`, onClose => (
            <Dialog yes={'fill'} no={'cancel'} onClose={yes => {
                onClose();
                if (yes) {
                    python_call('fill_property_with_terms', propertyName)
                        .then(() => this.updateStatus(
                            `Filled property "${propertyName}" with video keywords.`, true, true))
                        .catch(backend_error);
                }
            }}>
                <Cell className="text-center" center={true} full={true}>
                    <h3>Fill property "{propertyName}" with videos keywords (meta title and file path excluding extension)?</h3>
                </Cell>
            </Dialog>
        ));
    }
    editPropertyValue(name, value) {
        this.props.app.loadDialog(`Property "${name}", value "${value}"`, onClose => (
            <FormEditPropertyValue properties={this.generatePropTable(this.state.properties)} name={name} value={value} onClose={operation => {
                onClose();
                if (operation) {
                    switch (operation.form) {
                        case 'delete':
                            python_call('delete_property_value', name, value)
                                .then(() => this.updateStatus(`Property value deleted: "${name}" / "${value}"`, true))
                                .catch(backend_error)
                            break;
                        case 'edit':
                            python_call('edit_property_value', name, value, operation.value)
                                .then(() => this.updateStatus(`Property value edited: "${name}" : "${value}" -> "${operation.value}"`, true))
                                .catch(backend_error);
                            break;
                        case 'move':
                            python_call('move_property_value', name, value, operation.move)
                                .then(() => this.updateStatus(`Property value moved: "${value}" from "${name}" to "${operation.move}"`, true))
                                .catch(backend_error)
                            break;
                    }
                }
            }}/>
        ));
    }
}
