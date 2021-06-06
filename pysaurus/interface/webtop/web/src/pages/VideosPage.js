import {PAGE_SIZES, SEARCH_TYPE_TITLE, SOURCE_TREE} from "../utils/constants.js";
import {MenuPack} from "../components/MenuPack.js";
import {Pagination} from "../components/Pagination.js";
import {Video} from "../components/Video.js";
import {FormSourceVideo} from "../forms/FormSourceVideo.js";
import {FormGroup} from "../forms/FormGroup.js";
import {FormSearch} from "../forms/FormSearch.js";
import {FormSort} from "../forms/FormSort.js";
import {GroupView} from "../components/GroupView.js";
import {FormEditPropertyValue} from "../forms/FormEditPropertyValue.js";
import {FormFillKeywords} from "../forms/FormFillKeywords.js";
import {FormPropertyMultiVideo} from "../forms/FormPropertyMultiVideo.js";
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

export class VideosPage extends React.Component {
    constructor(props) {
        // parameters: {backend state}
        // app: App
        super(props);
        this.state = Object.assign({
            status: 'Loaded.',
            confirmDeletion: true,
            path: [],
            selector: new Selector(),
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
        this.updateStatus = this.updateStatus.bind(this);
        this.backend = this.backend.bind(this);

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
        const actions = this.features.actions;

        return (
            <div id="videos">
                <header className="horizontal">
                    <MenuPack title="Options">
                        <Menu title="Filter videos ...">
                            {<ActionToMenuItem action={actions.select}/>}
                            {<ActionToMenuItem action={actions.group}/>}
                            {<ActionToMenuItem action={actions.search}/>}
                            {<ActionToMenuItem action={actions.sort}/>}
                        </Menu>
                        {notFound || !nbVideos ? '' : <ActionToMenuItem action={actions.openRandomVideo}/>}
                        {<ActionToMenuItem action={actions.reload}/>}
                        {<ActionToMenuItem action={actions.manageProperties}/>}
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
                            {this.renderFilter()}
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
                                    groupDef={groupDef}
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
                               propDefs={this.state.properties}
                               selected={this.state.selector.has(data.video_id)}
                               onSelect={this.onVideoSelection}
                               onSelectPropertyValue={this.focusPropertyValue}
                               onInfo={this.updateStatus}
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
                        <div><ActionToSettingIcon action={actions.select}/></div>
                        {!compareSources(window.PYTHON_DEFAULT_SOURCES, sources) ?
                            <div><ActionToCross action={actions.unselect}/></div> : ''}
                    </td>
                </tr>
                <tr>
                    <td>
                        {groupDef ? (
                            <div>Grouped</div>
                        ) : <div className="no-filter">Ungrouped</div>}
                    </td>
                    <td>
                        <div>
                            <ActionToSettingIcon action={actions.group} title={groupDef ? 'Edit ...' : 'Group ...'}/>
                        </div>
                        {groupDef ? <div><ActionToCross action={actions.ungroup}/></div> : ''}
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
                            <ActionToSettingIcon action={actions.search} title={searchDef ? 'Edit ...' : 'Search ...'}/>
                        </div>
                        {searchDef ? <div><ActionToCross action={actions.unsearch}/></div> : ''}
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
                        <div><ActionToSettingIcon action={actions.sort}/></div>
                        {sortingIsDefault ? '' : <div><ActionToCross action={actions.unsort}/></div>}
                    </td>
                </tr>
                <tr>
                    <td>
                        {selectionSize ? (
                            <div>
                                <div>Selected</div>
                                <div>
                                    {selectedAll ? 'all' : ''}{" "}
                                    {selectionSize}{" "}
                                    {selectedAll ? '' : `/ ${realNbVideos}`}{" "}
                                    video{selectionSize < 2 ? '' : 's'}
                                </div>
                                <div className="mb-1">
                                    <button onClick={this.displayOnlySelected}>
                                        {this.state.displayOnlySelected ?
                                            'Display all videos' : 'Display only selected videos'}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div>No videos selected</div>
                        )}
                        {selectedAll ? '' : <div className="mb-1">
                            <button onClick={this.selectAll}>select all</button>
                        </div>}
                        {selectionSize ? (
                            <div className="mb-1">
                                <MenuPack title="Edit property ...">
                                    {this.state.properties.map((def, index) => (
                                        <MenuItem key={index}
                                                  action={() => this.editPropertiesForManyVideos(def.name)}>{def.name}</MenuItem>
                                    ))}
                                </MenuPack>
                            </div>
                        ) : ''}
                    </td>
                    <td>
                        {selectionSize ? <Cross title={`Deselect all`} action={this.deselect}/> : ''}
                    </td>
                </tr>
                </tbody>
            </table>
        );
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
        python_call("backend", callargs, pageSize, pageNumber, selector)
            .then(info => this.setState(Object.assign(state, info), top ? this.scrollTop : undefined))
            .catch(backend_error);
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
        this.setState({status: "Ready."});
    }

    unselectVideos() {
        this.backend(['set_sources', null], {pageNumber: 0});
    }

    selectVideos() {
        Fancybox.load(
            <FormSourceVideo tree={SOURCE_TREE} sources={this.state.sources} onClose={sources => {
                this.backend(['set_sources', sources], {pageNumber: 0});
            }}/>
        )
    }

    groupVideos() {
        const group_def = this.state.groupDef || {field: null, reverse: null};
        Fancybox.load(
            <FormGroup definition={group_def} properties={this.state.properties} onClose={criterion => {
                this.backend(['set_groups', criterion.field, criterion.sorting, criterion.reverse, criterion.allowSingletons, criterion.allowMultiple], {pageNumber: 0});
            }}/>
        )
    }

    backendGroupVideos(field, sorting = "count", reverse = true, allowSingletons = true, allowMultiple = true) {
        this.backend(['set_groups', field, sorting, reverse, allowSingletons, allowMultiple], {pageNumber: 0});
    }

    editPropertiesForManyVideos(propertyName) {
        const selectionSize = this.state.selector.size(this.state.realNbVideos);
        python_call('count_prop_values', propertyName, this.state.selector.toJSON())
            .then(valuesAndCounts => Fancybox.load(
                <FormPropertyMultiVideo nbVideos={selectionSize}
                                        definition={this.state.definitions[propertyName]}
                                        values={valuesAndCounts}
                                        onClose={edition => {
                                            python_call('edit_property_for_videos', propertyName, videos, edition.add, edition.remove)
                                                .then(() => this.backend(null, {status: `Edited property "${propertyName}" for ${selectionSize} video${selectionSize < 2 ? '' : 's'}`}))
                                                .catch(backend_error);
                                        }}/>
                )
            )
            .catch(backend_error);
    }

    searchVideos() {
        const search_def = this.state.searchDef || {text: null, cond: null};
        Fancybox.load(
            <FormSearch text={search_def.text} cond={search_def.cond} onClose={criterion => {
                this.backend(['set_search', criterion.text, criterion.cond], {pageNumber: 0});
            }}/>
        )
    }

    sortVideos() {
        Fancybox.load(
            <FormSort sorting={this.state.sorting} onClose={sorting => {
                this.backend(['set_sorting', sorting], {pageNumber: 0});
            }}/>
        )
    }

    resetGroup() {
        this.backend(['set_groups', ''], {pageNumber: 0});
    }

    resetSearch() {
        this.backend(['set_search', null, null], {pageNumber: 0});
    }

    resetSort() {
        this.backend(['set_sorting', null], {pageNumber: 0});
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
        Fancybox.load(
            <FormFillKeywords properties={this.getStringSetProperties(this.state.properties)} onClose={state => {
                python_call('fill_property_with_terms', state.field, state.onlyEmpty)
                    .then(() => this.backend(null, {status: `Filled property "${state.field}" with video keywords.`}))
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
        Fancybox.load(
            <FormEditPropertyValue properties={this.state.definitions}
                                   name={name}
                                   values={values}
                                   onClose={operation => {
                                       switch (operation.form) {
                                           case 'delete':
                                               this.backend(['delete_property_value', name, values], {status: `Property value deleted: "${name}" / "${values.join('", "')}"`});
                                               break;
                                           case 'edit':
                                               this.backend(['edit_property_value', name, values, operation.value], {status: `Property value edited: "${name}" : "${values.join('", "')}" -> "${operation.value}"`});
                                               break;
                                           case 'move':
                                               this.backend(['move_property_value', name, values, operation.move], {status: `Property value moved: "${values.join('", "')}" from "${name}" to "${operation.move}"`});
                                               break;
                                       }
                                   }}/>
        )
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
        python_call('set_groups', `:${propertyName}`, "count", true, true, true)
            .then(() => this.backend(['classifier_select_group_by_value', propertyValue], {pageNumber: 0}))
            .catch(backend_error);
    }
}
