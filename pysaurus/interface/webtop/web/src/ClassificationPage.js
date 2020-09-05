import {SettingIcon, Cross} from "./buttons.js";
import {PAGE_SIZES, VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER} from "./constants.js";
import {MenuPack, MenuItem, Menu, MenuItemCheck} from "./MenuPack.js";
import {Pagination} from "./Pagination.js";
import {ReadOnlyVideo} from "./ReadOnlyVideo.js";
import {GroupView} from "./GroupView.js";

export class ClassificationPage extends React.Component {
    parametersToState(parameters, state) {
        state.properties = parameters.properties;
        state.property = parameters.property;
        state.path = parameters.path;
        state.groups = parameters.groups;
        state.videos = parameters.videos;
    }
    constructor(props) {
        // parameters: {properties, property, path, groups, videos}
        // app: App
        super(props);
        this.state = {
            status: 'Loaded.',
            pageSize: VIDEO_DEFAULT_PAGE_SIZE,
            pageNumber: VIDEO_DEFAULT_PAGE_NUMBER,
            stackFilter: false,
            stackGroup: false,
            groupID: 0
        };
        this.parametersToState = this.parametersToState.bind(this);
        this.back = this.back.bind(this);
        this.changePage = this.changePage.bind(this);
        this.unstack = this.unstack.bind(this);
        this.showGroup = this.showGroup.bind(this);
        this.selectGroup = this.selectGroup.bind(this);
        this.resetStatus = this.resetStatus.bind(this);
        this.setPageSize = this.setPageSize.bind(this);
        this.scrollTop = this.scrollTop.bind(this);
        this.stackGroup = this.stackGroup.bind(this);
        this.stackFilter = this.stackFilter.bind(this);
        this.concatenatePath = this.concatenatePath.bind(this);

        this.parametersToState(this.props.parameters, this.state);
    }
    render() {
        const nbVideos = this.state.videos.length;
        const nbPages = Math.floor(nbVideos / this.state.pageSize) + (nbVideos % this.state.pageSize ? 1: 0);
        const stringProperties = this.getStringProperties(this.state.properties);

        return (
            <div id="videos" className="classifier">
                <header className="horizontal">
                    <button onClick={this.back}>&#11164;</button>
                    <strong className="classifier-title">
                        Classifier for <em>"{this.state.property}"</em>
                    </strong>
                    <MenuPack title="Videos page size ...">
                        {PAGE_SIZES.map((count, index) => (
                            <MenuItemCheck key={index}
                                           checked={this.state.pageSize === count}
                                           action={checked => {if (checked) this.setPageSize(count);}}>
                                {count} video{count > 1 ? 's' : ''} per page
                            </MenuItemCheck>
                        ))}
                    </MenuPack>
                    {this.state.path.length > 1 && stringProperties.length ? (
                        <MenuPack title="Concatenate path into ...">
                            {stringProperties.map((def, i) => (
                                <MenuItem key={i} action={() => this.concatenatePath(def.name)}>{def.name}</MenuItem>
                            ))}
                        </MenuPack>
                    ) : ''}
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
                                    {this.state.path.map((value, index) => (
                                        <div key={index} className="path-step horizontal">
                                            <div className="title">{value.toString()}</div>
                                            {index === this.state.path.length - 1 ? (
                                                <div className="icon">
                                                    <Cross title="unstack" action={this.unstack}/>
                                                </div>
                                            ) : ''}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
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
                                    <GroupView key={this.state.path.join('-')}
                                               groupID={this.state.groupID}
                                               field={`:${this.state.property}`}
                                               sorting={"field"}
                                               reverse={false}
                                               groups={this.state.groups}
                                               onSelect={this.showGroup}
                                               onPlus={this.selectGroup}/>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="main-panel videos">{this.renderVideos()}</div>
                </div>
                <footer className="horizontal">
                    <div className="footer-status" onClick={this.resetStatus}>{this.state.status}</div>
                    <div className="footer-information">
                        <div className="info group">
                            Group {this.state.groupID + 1}/{this.state.groups.length}
                        </div>
                        <div className="info count">{nbVideos} video{nbVideos > 1 ? 's' : ''}</div>
                    </div>
                </footer>
            </div>
        );
    }
    renderVideos() {
        const start = this.state.pageSize * this.state.pageNumber;
        const end = Math.min(start + this.state.pageSize, this.state.videos.length);
        return this.state.videos.slice(start, end).map((data, index) => (
            <ReadOnlyVideo key={data.video_id}
                           data={data}
                           index={index}
                           propDefs={this.state.properties}
                           parent={this}/>
        ));
    }

    back() {
        this.props.app.loadVideosPage();
    }
    changePage(pageNumber) {
        this.setState({pageNumber}, this.scrollTop);
    }
    unstack() {
        python_call('classifier_back', this.state.property, this.state.path)
            .then(data => this.setState({
                groupID: 0,
                pageNumber: 0,
                path: data.path,
                groups: data.groups,
                videos: data.videos,
            }))
            .catch(backend_error);
    }
    showGroup(index) {
        python_call('classifier_show_group', index)
            .then(data => this.setState({groupID: index, videos: data.videos}))
            .catch(backend_error);
    }
    selectGroup(index) {
        python_call('classifier_select_group', this.state.property, this.state.path, index)
            .then(data => this.setState({
                groupID: 0,
                pageNumber: 0,
                path: data.path,
                groups: data.groups,
                videos: data.videos,
            }))
            .catch(backend_error);
    }
    updateStatus(status) {
        this.setState({status});
    }
    resetStatus() {
        this.setState({status: "Ready."});
    }
    setPageSize(count) {
        if (count !== this.state.pageSize)
            this.setState({pageSize: count, pageNumber: 0}, this.scrollTop);
    }
    scrollTop() {
        const videos = document.querySelector('#videos .videos');
        videos.scrollTop = 0;
    }
    stackGroup() {
        this.setState({stackGroup: !this.state.stackGroup});
    }
    stackFilter() {
        this.setState({stackFilter: !this.state.stackFilter});
    }
    concatenatePath(outputPropertyName) {
        python_call('classifier_concatenate_path', this.state.path, this.state.property, outputPropertyName)
            .then(data => this.setState({
                groupID: 0,
                pageNumber: 0,
                path: [],
                groups: data.groups,
                videos: data.videos,
            }))
            .catch(backend_error);
    }
    getStringProperties(definitions) {
        const properties = [];
        for (let def of definitions) {
            if (def.type === "str" && def.name !== this.state.property)
                properties.push(def);
        }
        return properties;
    }
}
