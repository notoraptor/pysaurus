import {SettingIcon, Cross} from "./buttons.js";
import {FIELD_TITLES, PAGE_SIZES, FIELDS, SEARCH_TYPE_TITLE} from "./constants.js";
import {MenuPack, MenuItem, Menu, MenuItemCheck} from "./MenuPack.js";
import {Pagination} from "./Pagination.js";
import {Video} from "./Video.js";
import {FormSourceVideo} from "./FormSourceVideo.js";
import {FormGroup} from "./FormGroup.js";
import {FormSearch} from "./FormSearch.js";
import {FormSort} from "./FormSort.js";

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
        const backend = this.props.page.state.info;
        const sources = backend.sources;
        const groupDef = backend.groupDef;
        const groupFieldValue = backend.groupFieldValue;
        const searchDef = backend.searchDef;
        const sorting = backend.sorting;
        const sortingIsDefault = sorting.length === 1 && sorting[0] === '-date';
        return (
            <table className="filter">
                <tbody>
                <tr>
                    <td className="left">
                        {sources.map((source, index) => (
                            <div className="source" key={index}>
                                {source.join(' ').replace('_', ' ')}
                            </div>
                        ))}
                    </td>
                    <td className="right"><SettingIcon title={`Select sources ... (${SHORTCUTS.select})`} action={app.selectVideos}/></td>
                </tr>
                <tr>
                    <td className="left">
                        {groupDef ? (
                            <div className="filter">
                                <div>Grouped by</div>
                                <div>
                                    {FIELD_TITLES[groupDef.field]}{' '}
                                    {groupDef.reverse ? (<span>&#9660;</span>) : (<span>&#9650;</span>)}
                                </div>
                                {groupDef.nb_groups ? (
                                    <div>
                                        <div>Group {groupDef.group_id + 1} / {groupDef.nb_groups}</div>
                                        <div>
                                            {Utils.sentence(FIELD_TITLES[groupDef.field])}:{' '}
                                            <strong>{groupFieldValue}</strong>
                                        </div>
                                    </div>
                                ) : ''}
                            </div>
                        ) : <div className="no-filter">Ungrouped</div>}
                    </td>
                    <td className="right">
                        <div><SettingIcon title={(groupDef ? 'Edit ...' : 'Group ...') + ` (${SHORTCUTS.group})`} action={app.groupVideos}/></div>
                        {groupDef ? <div><Cross title="Reset group" action={app.resetGroup}/></div> : ''}
                    </td>
                </tr>
                <tr>
                    <td className="left">
                        {searchDef ? (
                            <div className="filter">
                                <div>Searched {SEARCH_TYPE_TITLE[searchDef.cond]}</div>
                                <div>&quot;<strong>{searchDef.text}</strong>&quot;</div>
                            </div>
                        ) : <div className="no-filter">No search</div>}
                    </td>
                    <td className="right">
                        <div>
                            <SettingIcon title={(searchDef ? 'Edit ...' : 'Search ...') + ` (${SHORTCUTS.search})`} action={app.searchVideos}/>
                        </div>
                        {searchDef ? <div><Cross title="reset search" action={app.resetSearch}/></div> : ''}
                    </td>
                </tr>
                <tr>
                    <td className="left">
                        <div>Sorted by</div>
                        {sorting.map((val, i) => (
                            <div key={i}>
                                <strong>{val.substr(1)}</strong>{' '}
                                {val[0] === '-' ? (<span>&#9660;</span>) : (<span>&#9650;</span>)}
                            </div>))}
                    </td>
                    <td className="right">
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
            info: args.info,
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
            [SHORTCUTS.manageProperties]: this.manageProperties,
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

        return (
            <div id="videos">
                <header className="horizontal">
                    <MenuPack title="Options">
                        <Menu title="Filter videos ...">
                            <MenuItem shortcut={SHORTCUTS.select} action={this.selectVideos}>Select videos ...</MenuItem>
                            <MenuItem shortcut={SHORTCUTS.group} action={this.selectVideos}>Group ...</MenuItem>
                            <MenuItem shortcut={SHORTCUTS.search} action={this.selectVideos}>Search ...</MenuItem>
                            <MenuItem shortcut={SHORTCUTS.sort} action={this.selectVideos}>Sort ...</MenuItem>
                        </Menu>
                        {notFound || !nbVideos ? '' : <MenuItem action={this.openRandomVideo}>Open random video</MenuItem>}
                        <MenuItem shortcut={SHORTCUTS.reload} action={this.reloadDatabase}>Reload database ...</MenuItem>
                        <MenuItem shortcut={SHORTCUTS.manageProperties} action={this.manageProperties}>Manage properties</MenuItem>
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
                        {group_def ? (
                            <Pagination singular="group"
                                        plural="groups"
                                        nbPages={group_def.nb_groups}
                                        pageNumber={group_def.group_id}
                                        onChange={this.changeGroup}/>
                        ) : ''}
                        <Pagination singular="page"
                                    plural="pages"
                                    nbPages={nbPages}
                                    pageNumber={this.state.pageNumber}
                                    onChange={this.changePage}/>
                    </div>
                </header>
                <div className="frontier"/>
                <div className="content">
                    <div className="wrapper">
                        <div className="side-panel">
                            <Filter page={this} />
                        </div>
                        <div className="main-panel videos">{this.renderVideos()}</div>
                    </div>
                </div>
                <footer className="horizontal">
                    <div className="footer-status" onClick={this.resetStatus}>{this.state.status}</div>
                    <div className="footer-information">
                        <div className="info count">{nbVideos} video{nbVideos > 1 ? 's' : ''}</div>
                        <div className="info size">{validSize}</div>
                        <div className="info length">{validLength}</div>
                    </div>
                </footer>
            </div>
        );
    }
    renderVideos() {
        return this.state.info.videos.map(data => (
            <Video key={data.video_id} data={data} index={data.local_id} parent={this} confirmDeletion={this.state.confirmDeletion}/>
        ));
    }
    scrollTop() {
        const videos = document.querySelector('#videos .videos');
        videos.scrollTop = 0;
    }
    updatePage(state, top = true) {
        const pageSize = state.pageSize !== undefined ? state.pageSize: this.state.pageSize;
        const pageNumber = state.pageNumber !== undefined ? state.pageNumber: this.state.pageNumber;
        python_call('get_info_and_videos', pageSize, pageNumber, FIELDS)
            .then(info => {
                state.pageSize = pageSize;
                state.pageNumber = pageNumber;
                state.info = info;
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
        this.props.app.loadDialog('Select Videos', onClose => (
            <FormSourceVideo tree={this.state.info.sourceTree} sources={this.state.info.sources} onClose={sources => {
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
        const group_def = this.state.info.groupDef || {field: null, reverse: null};
        this.props.app.loadDialog('Group videos with same:', onClose => (
            <FormGroup field={group_def.field} reverse={group_def.reverse} onClose={criterion => {
                onClose();
                if (criterion) {
                    python_call('group_videos', criterion.field, criterion.reverse)
                        .then(() => this.updatePage({pageNumber: 0}))
                        .catch(backend_error);
                }
            }} />
        ));
    }
    searchVideos() {
        const search_def = this.state.info.searchDef || {text: null, cond: null};
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
        const sorting = this.state.info.sorting;
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
        python_call('group_videos', null, null)
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
    changePage(pageNumber) {
        this.updatePage({pageNumber});
    }
}
