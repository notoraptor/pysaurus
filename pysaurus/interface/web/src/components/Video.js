import {MenuPack} from "./MenuPack.js";
import {FormVideoRename} from "../forms/FormVideoRename.js";
import {Dialog} from "../dialogs/Dialog.js";
import {FormVideoEditProperties} from "../forms/FormVideoEditProperties.js";
import {Collapsable} from "./Collapsable.js";
import {MenuItem} from "./MenuItem.js";
import {Menu} from "./Menu.js";
import {backend_error, python_call} from "../utils/backend.js";
import {Characters} from "../utils/constants.js";

window.LATEST_MOVE_FOLDER = null;

export class Video extends React.Component {
    constructor(props) {
        super(props);
        this.openVideo = this.openVideo.bind(this);
        this.confirmDeletion = this.confirmDeletion.bind(this);
        this.deleteVideo = this.deleteVideo.bind(this);
        this.openContainingFolder = this.openContainingFolder.bind(this);
        this.copyMetaTitle = this.copyMetaTitle.bind(this);
        this.copyFileTitle = this.copyFileTitle.bind(this);
        this.copyFilePath = this.copyFilePath.bind(this);
        this.copyVideoID = this.copyVideoID.bind(this);
        this.renameVideo = this.renameVideo.bind(this);
        this.editProperties = this.editProperties.bind(this);
        this.onSelect = this.onSelect.bind(this);
        this.reallyDeleteVideo = this.reallyDeleteVideo.bind(this);
        this.confirmMove = this.confirmMove.bind(this);
        this.moveVideo = this.moveVideo.bind(this);
    }

    render() {
        return this.props.data.readable ? this.renderVideo() : this.renderVideoState();
    }

    renderVideo() {
        const data = this.props.data;
        const audio_bit_rate = Math.round(data.audio_bit_rate / 1000);
        data.extension = data.extension.toUpperCase();
        data.frame_rate = Math.round(data.frame_rate);
        data.quality = Math.round(data.quality * 100) / 100;
        const title = data.title;
        const file_title = data.file_title;
        const meta_title = (title === file_title ? null : title);
        const hasThumbnail = data.has_thumbnail;
        const htmlID = `video-${data.video_id}`;
        const alreadyOpened = APP_STATE.videoHistory.has(data.filename);
        return (
            <div className={'video horizontal' + (data.exists ? ' found' : ' not-found')}>
                <div className="image p-2">
                    {hasThumbnail ?
                        <img alt={data.title} src={data.thumbnail_path}/> :
                        <div className="no-thumbnail">no thumbnail</div>}
                </div>
                <div className="video-details horizontal flex-grow-1">
                    {this.renderProperties()}
                    <div className="info p-2">
                        <div className="name">
                            <div className="options horizontal">
                                <MenuPack title={`${Characters.SETTINGS}`}>
                                    {data.exists ?
                                        <MenuItem action={this.openVideo}>Open file</MenuItem> :
                                        <div className="text-center bold">(not found)</div>}
                                    {data.exists ?
                                        <MenuItem action={this.openContainingFolder}>
                                            Open containing folder
                                        </MenuItem> : ''}
                                    {meta_title ? <MenuItem action={this.copyMetaTitle}>Copy meta title</MenuItem> : ''}
                                    {file_title ? <MenuItem action={this.copyFileTitle}>Copy file title</MenuItem> : ''}
                                    <MenuItem action={this.copyFilePath}>Copy path</MenuItem>
                                    <MenuItem action={this.copyVideoID}>Copy video ID</MenuItem>
                                    {data.exists ? <MenuItem action={this.renameVideo}>Rename video</MenuItem> : ''}
                                    {data.exists ? <MenuItem action={this.moveVideo}>Move video to another folder ...</MenuItem> : ""}
                                    <MenuItem className="red-flag" action={this.deleteVideo}>
                                        {data.exists ? 'Delete video' : 'Delete entry'}
                                    </MenuItem>
                                    {this.props.groupedByMoves && data.moves.length ? (
                                        <Menu title="Confirm move to ...">
                                            {data.moves.map((dst, index) => (
                                                <MenuItem key={index}
                                                          className="confirm-move"
                                                          action={() => this.confirmMove(data.video_id, dst.video_id)}>
                                                    <code>{dst.filename}</code>
                                                </MenuItem>
                                            ))}
                                        </Menu>
                                    ) : ""}
                                </MenuPack>
                                <div>
                                    <input type="checkbox"
                                           checked={this.props.selected}
                                           id={htmlID}
                                           onChange={this.onSelect}/>
                                    &nbsp;
                                    <label htmlFor={htmlID}><strong className="title">{data.title}</strong></label>
                                </div>
                            </div>
                            {data.title === data.file_title ? '' :
                                <div className="file-title"><em>{data.file_title}</em></div>}
                        </div>
                        <div className={'filename-line' + (data.exists ? '' : ' horizontal')}>
                            {data.exists ? '' :
                                <div className="prepend clickable" onClick={this.deleteVideo}>
                                    <code className="text-not-found">NOT FOUND</code>
                                    <code className="text-delete">DELETE</code>
                                </div>}
                            <div className={`filename ${alreadyOpened ? "already-opened" : ""}`}>
                                <code {...(data.exists ? {className: "clickable"} : {})} {...(data.exists ? {onClick: this.openVideo} : {})}>{data.filename}</code>
                            </div>
                        </div>
                        <div className="format horizontal">
                            <div className="prepend"><code>{data.extension}</code></div>
                            <div>
                                <strong title={data.file_size}>{data.size}</strong> / {data.container_format}{" "}
                                (<span title={data.video_codec_description}>{data.video_codec}</span>,{" "}
                                <span title={data.audio_codec_description}>{data.audio_codec}</span>)
                            </div>
                            <div className="prepend"><code>Quality</code></div>
                            <div><strong><em>{data.quality}</em></strong> %</div>
                        </div>
                        <div>
                            <strong>{data.width}</strong> x <strong>{data.height}</strong> @{" "}
                            {data.frame_rate} fps, {data.bit_depth} bits | {data.sample_rate} Hz,{" "}
                            <span title={data.audio_bit_rate}>{audio_bit_rate} Kb/s</span> |{" "}
                            <strong>{data.length}</strong> | <code>{data.date}</code>
                        </div>
                        {data.similarity_id !== null && data.similarity_id > -1 ? (
                            <div>
                                <strong>Similarity ID:</strong> <code>{data.similarity_id}</code>
                            </div>
                        ) : ""}
                        {this.props.groupedByMoves && data.moves.length === 1 ? (
                            <p>
                                <button className="block"
                                        onClick={() => this.confirmMove(data.video_id, data.moves[0].video_id)}>
                                    <strong>Confirm move to:</strong><br/><code>{data.moves[0].filename}</code>
                                </button>
                            </p>
                        ) : ""}
                    </div>
                </div>
            </div>
        );
    }

    renderVideoState() {
        const data = this.props.data;
        const errors = data.errors.slice();
        errors.sort();
        const alreadyOpened = APP_STATE.videoHistory.has(data.filename);
        return (
            <div className={'video horizontal' + (data.exists ? ' found' : ' not-found')}>
                <div className="image p-2">
                    <div className="no-thumbnail">no thumbnail</div>
                </div>
                <div className="video-details horizontal flex-grow-1">
                    <div className="info p-2">
                        <div className="name">
                            <div className="options horizontal">
                                <MenuPack title={`${Characters.SETTINGS}`}>
                                    {data.exists ?
                                        <MenuItem action={this.openVideo}>Open file</MenuItem> :
                                        <div className="text-center bold">(not found)</div>}
                                    {data.exists ?
                                        <MenuItem action={this.openContainingFolder}>
                                            Open containing folder
                                        </MenuItem> : ''}
                                    <MenuItem action={this.copyFileTitle}>Copy file title</MenuItem>
                                    <MenuItem action={this.copyFilePath}>Copy path</MenuItem>
                                    {data.exists ? <MenuItem action={this.renameVideo}>Rename video</MenuItem> : ''}
                                    <MenuItem className="red-flag" action={this.deleteVideo}>
                                        {data.exists ? 'Delete video' : 'Delete entry'}
                                    </MenuItem>
                                </MenuPack>
                                <div><strong className="title">{data.file_title}</strong></div>
                            </div>
                        </div>
                        <div className={'filename-line' + (data.exists ? '' : ' horizontal')}>
                            {data.exists ? '' :
                                <div className="prepend clickable" onClick={this.deleteVideo}>
                                    <code className="text-not-found">NOT FOUND</code>
                                    <code className="text-delete">DELETE</code>
                                </div>}
                            <div className={`filename ${alreadyOpened ? "already-opened" : ""}`}>
                                <code {...(data.exists ? {className: "clickable"} : {})} {...(data.exists ? {onClick: this.openVideo} : {})}>{data.filename}</code>
                            </div>
                        </div>
                        <div className="format horizontal">
                            <div className="prepend"><code>{data.extension}</code></div>
                            <div><strong title={data.file_size}>{data.size}</strong></div>
                            {" | "}
                            <div><code>{data.date}</code></div>
                        </div>
                        <div className="horizontal">
                            <div>
                                <strong>Video unreadable:</strong>
                            </div>
                            <div>
                                <div className="property">
                                    {errors.map((element, elementIndex) => (
                                        <span className="value" key={elementIndex}>{element.toString()}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    renderProperties() {
        const props = this.props.data.properties;
        const propDefs = this.props.propDefs;
        if (!propDefs.length)
            return '';
        return (
            <div className="properties p-2">
                <div className="edit-properties clickable text-center mb-2" onClick={this.editProperties}>PROPERTIES</div>
                {propDefs.map(def => {
                    const name = def.name;
                    const value = props.hasOwnProperty(name) ? props[name] : def.defaultValue;
                    let noValue;
                    if (def.multiple)
                        noValue = !value.length;
                    else
                        noValue = def.type === "str" && !value;
                    let printableValues = def.multiple ? value : [value];
                    return noValue ? '' : (
                        <div key={name} className={`property ${props.hasOwnProperty(name) ? "defined" : ""}`}>
                            <Collapsable title={name}>
                                {!noValue ? (printableValues.map((element, elementIndex) => (
                                    <span className="value clickable"
                                          key={elementIndex}
                                          onClick={() => this.props.onSelectPropertyValue(name, element)}>
                                        {element.toString()}
                                    </span>
                                ))) : <span className="no-value">no value</span>}
                            </Collapsable>
                        </div>
                    );
                })}
            </div>
        );
    }

    openVideo() {
        python_call('open_video', this.props.data.video_id)
            .then(() => {
                APP_STATE.videoHistory.add(this.props.data.filename);
                this.props.onInfo('Opened: ' + this.props.data.filename)
            })
            .catch(() => this.props.onInfo('Unable to open: ' + this.props.data.filename));
    }

    editProperties() {
        const data = this.props.data;
        Fancybox.load(
            <FormVideoEditProperties data={data} definitions={this.props.propDefs} onClose={properties => {
                python_call('set_video_properties', this.props.data.video_id, properties)
                    .then(() => this.props.onInfo(`Properties updated: ${data.filename}`, true))
                    .catch(backend_error);
            }}/>
        );
    }

    confirmDeletion() {
        const filename = this.props.data.filename;
        const thumbnail_path = this.props.data.thumbnail_path;
        Fancybox.load(
            <Dialog title="Confirm deletion" yes="delete" action={this.reallyDeleteVideo}>
                <div className="form-delete-video text-center bold">
                    <h2>Are you sure you want to <strong className="red-flag">definitely</strong> delete this video?</h2>
                    <div className="details overflow-auto px-2 py-1"><code id="filename">{filename}</code></div>
                    <p>
                        {this.props.data.has_thumbnail ? (
                            <img id="thumbnail" alt="No thumbnail available" src={thumbnail_path}/>
                        ) : (
                            <div className="no-thumbnail">no thumbnail</div>
                        )}
                    </p>
                </div>
            </Dialog>
        );
    }

    deleteVideo() {
        if (this.props.data.exists || this.props.confirmDeletion)
            this.confirmDeletion();
        else
            this.reallyDeleteVideo();
    }

    reallyDeleteVideo() {
        python_call('delete_video', this.props.data.video_id)
            .then(() => this.props.onInfo('Video deleted! ' + this.props.data.filename, true))
            .catch(backend_error);
    }

    openContainingFolder() {
        python_call('open_containing_folder', this.props.data.video_id)
            .then(folder => {
                this.props.onInfo(`Opened folder: ${folder}`);
            })
            .catch(backend_error);
    }

    copyMetaTitle() {
        const text = this.props.data.title;
        python_call('clipboard', text)
            .then(() => this.props.onInfo('Copied to clipboard: ' + text))
            .catch(() => this.props.onInfo(`Cannot copy meta title to clipboard: ${text}`));
    }

    copyFileTitle() {
        const text = this.props.data.file_title;
        python_call('clipboard', text)
            .then(() => this.props.onInfo('Copied to clipboard: ' + text))
            .catch(() => this.props.onInfo(`Cannot copy file title to clipboard: ${text}`));
    }

    copyFilePath() {
        python_call('clipboard_video_path', this.props.data.video_id)
            .then(() => this.props.onInfo('Copied to clipboard: ' + this.props.data.filename))
            .catch(() => this.props.onInfo(`Cannot copy file path to clipboard: ${this.props.data.filename}`));
    }

    copyVideoID() {
        python_call('clipboard', this.props.data.video_id)
            .then(() => this.props.onInfo('Copied to clipboard: ' + this.props.data.video_id))
            .catch(() => this.props.onInfo(`Cannot copy video ID to clipboard: ${this.props.data.video_id}`));
    }

    confirmMove(srcID, dstID) {
        python_call("move_video", srcID, dstID)
            .then(() => this.props.onInfo(`Moved: ${this.props.data.filename}`, true))
            .catch(backend_error);
    }

    renameVideo() {
        const filename = this.props.data.filename;
        const title = this.props.data.file_title;
        Fancybox.load(
            <FormVideoRename filename={filename} title={title} onClose={newTitle => {
                python_call('rename_video', this.props.data.video_id, newTitle)
                    .then(() => this.props.onInfo(`Renamed: ${newTitle}`, true))
                    .catch(backend_error);
            }}/>
        );
    }

    moveVideo() {
        python_call("select_directory", window.LATEST_MOVE_FOLDER)
            .then(directory => {
                if (directory) {
                    window.LATEST_MOVE_FOLDER = directory;
                    this.props.onMove(this.props.data.video_id, directory);
                }
            })
            .catch(backend_error);
    }

    onSelect(event) {
        if (this.props.onSelect) {
            this.props.onSelect(this.props.data.video_id, event.target.checked);
        }
    }
}

Video.propTypes = {
    data: PropTypes.object.isRequired,
    propDefs: PropTypes.arrayOf(PropTypes.object).isRequired,
    confirmDeletion: PropTypes.bool,
    groupedByMoves: PropTypes.bool,
    selected: PropTypes.bool,
    // onSelect(videoID, selected)
    onSelect: PropTypes.func,
    // onSelectPropertyValue(propName, propVal)
    onSelectPropertyValue: PropTypes.func.isRequired,
    // onInfo(message: str, backendUpdated: bool)
    onInfo: PropTypes.func.isRequired,
    // onMove(videoID, directory)
    onMove: PropTypes.func.isRequired,
};
