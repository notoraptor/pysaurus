import {MenuPack} from "./MenuPack.js";
import {FormVideoRename} from "../forms/FormVideoRename.js";
import {Dialog} from "../dialogs/Dialog.js";
import {FormVideoEditProperties} from "../forms/FormVideoEditProperties.js";
import {Collapsable} from "./Collapsable.js";
import {MenuItem} from "./MenuItem.js";
import {Menu} from "./Menu.js";
import {backend_error, python_call} from "../utils/backend.js";
import {Characters} from "../utils/constants.js";
import {formatString} from "../utils/functions.js";

/**
 * Generate class name for common value of videos grouped by similarity
 * @param value {boolean?}
 * @returns {string}
 */
function cc(value) {
    return value === undefined ? "" : (value ? "common-true" : "common-false");
}


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
        this.dismissSimilarity = this.dismissSimilarity.bind(this);
        this.reallyDismissSimilarity = this.reallyDismissSimilarity.bind(this);
        this.resetSimilarity = this.resetSimilarity.bind(this);
        this.reallyResetSimilarity = this.reallyResetSimilarity.bind(this);
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
        const common = (this.props.groupDef && this.props.groupDef.common) || {};
        const groupedBySimilarityID = this.props.groupDef && this.props.groupDef.field === "similarity_id";
        return (
            <div className={'video horizontal' + (data.found ? ' found' : ' not-found')}>
                <div className="image p-2">
                    {hasThumbnail ?
                        <img alt={data.title} src={data.thumbnail_path}/> :
                        <div className="no-thumbnail">{PYTHON_LANG.text_no_thumbnail}</div>}
                </div>
                <div className="video-details horizontal flex-grow-1">
                    {this.renderProperties()}
                    <div className="info p-2">
                        <div className="name">
                            <div className="options horizontal">
                                <MenuPack title={`${Characters.SETTINGS}`}>
                                    {data.found ?
                                        <MenuItem action={this.openVideo}>{PYTHON_LANG.action_open_file}</MenuItem> :
                                        <div className="text-center bold">{PYTHON_LANG.text_not_found}</div>}
                                    {data.found ?
                                        <MenuItem action={this.openContainingFolder}>
                                            {PYTHON_LANG.action_open_containing_folder}
                                        </MenuItem> : ""}
                                    {meta_title ? <MenuItem action={this.copyMetaTitle}>{PYTHON_LANG.action_copy_meta_title}</MenuItem> : ""}
                                    {file_title ? <MenuItem action={this.copyFileTitle}>{PYTHON_LANG.action_copy_file_title}</MenuItem> : ""}
                                    <MenuItem action={this.copyFilePath}>{PYTHON_LANG.action_copy_path}</MenuItem>
                                    <MenuItem action={this.copyVideoID}>{PYTHON_LANG.action_copy_video_id}</MenuItem>
                                    {data.found ? <MenuItem action={this.renameVideo}>{PYTHON_LANG.action_rename_video}</MenuItem> : ""}
                                    {data.found ?
                                        <MenuItem action={this.moveVideo}>{PYTHON_LANG.action_move_video_to_another_folder}</MenuItem>
                                        : ""}
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
                                    {groupedBySimilarityID ? (
                                        <MenuItem action={this.dismissSimilarity}>{PYTHON_LANG.action_dismiss_similarity}</MenuItem>
                                    ) : ""}
                                    {data.similarity_id !== null ? (
                                        <MenuItem action={this.resetSimilarity}>{PYTHON_LANG.action_reset_similarity}</MenuItem>
                                    ) : ""}
                                    <MenuItem className="red-flag" action={this.deleteVideo}>
                                        {data.found ? PYTHON_LANG.text_delete_video : PYTHON_LANG.text_delete_entry}
                                    </MenuItem>
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
                            {data.title === data.file_title ? "" :
                                <div className="file-title"><em>{data.file_title}</em></div>}
                        </div>
                        <div className={'filename-line' + (data.found ? "" : ' horizontal')}>
                            {data.found ? "" :
                                <div className="prepend clickable" onClick={this.deleteVideo}>
                                    <code className="text-not-found">{PYTHON_LANG.text_not_found_uppercase}</code>
                                    <code className="text-delete">{PYTHON_LANG.text_delete}</code>
                                </div>}
                            <div className={`filename ${alreadyOpened ? "already-opened" : ""}`}>
                                <code {...(data.found ? {className: "clickable"} : {})} {...(data.found ? {onClick: this.openVideo} : {})}>{data.filename}</code>
                            </div>
                        </div>
                        <div className="format horizontal">
                            <div className="prepend">
                                <code className={cc(common.extension)}>{data.extension}</code>
                            </div>
                            <div>
                                <strong title={data.file_size} className={cc(common.size)}>{data.size}</strong> /{" "}
                                <span className={cc(common.container_format)}>{data.container_format}</span>{" "}
                                (<span title={data.video_codec_description}
                                       className={cc(common.video_codec)}>{data.video_codec}</span>,{" "}
                                <span title={data.audio_codec_description}
                                      className={cc(common.audio_codec)}>{data.audio_codec}</span>)
                            </div>
                            <div className="prepend"><code>Quality</code></div>
                            <div className={cc(common.quality)}><strong><em>{data.quality}</em></strong> %</div>
                        </div>
                        <div>
                            <strong className={cc(common.width)}>{data.width}</strong> x{" "}
                            <strong className={cc(common.height)}>{data.height}</strong> @{" "}
                            <span className={cc(common.frame_rate)}>{data.frame_rate} {PYTHON_LANG.suffix_fps}</span>,{" "}
                            <span className={cc(common.bit_depth)}>{data.bit_depth} {PYTHON_LANG.text_bits}</span> |{" "}
                            <span className={cc(common.sample_rate)}>{data.sample_rate} {PYTHON_LANG.suffix_hertz}</span>,{" "}
                            <span title={data.audio_bit_rate}
                                  className={cc(common.audio_bit_rate)}>{audio_bit_rate} {PYTHON_LANG.suffix_kbps}</span> |{" "}
                            <strong className={cc(common.length)}>{data.length}</strong> | <code
                            className={cc(common.date)}>{data.date}</code>
                        </div>
                        {!groupedBySimilarityID ? (
                            <div>
                                <strong>{PYTHON_LANG.text_similarity_id}:</strong>{" "}
                                <code>
                                    {data.similarity_id === null ?
                                        PYTHON_LANG.text_not_yet_compared :
                                        (data.similarity_id === -1 ?
                                            PYTHON_LANG.text_no_similarities :
                                            data.similarity_id)}
                                </code>
                            </div>
                        ) : ""}
                        {this.props.groupedByMoves && data.moves.length === 1 ? (
                            <p>
                                <button className="block"
                                        onClick={() => this.confirmMove(data.video_id, data.moves[0].video_id)}>
                                    <strong>{PYTHON_LANG.text_confirm_move_to}:</strong><br/><code>{data.moves[0].filename}</code>
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
            <div className={'video horizontal' + (data.found ? ' found' : ' not-found')}>
                <div className="image p-2">
                    <div className="no-thumbnail">{PYTHON_LANG.text_no_thumbnail}</div>
                </div>
                <div className="video-details horizontal flex-grow-1">
                    <div className="info p-2">
                        <div className="name">
                            <div className="options horizontal">
                                <MenuPack title={`${Characters.SETTINGS}`}>
                                    {data.found ?
                                        <MenuItem action={this.openVideo}>{PYTHON_LANG.action_open_file}</MenuItem> :
                                        <div className="text-center bold">{PYTHON_LANG.text_not_found}</div>}
                                    {data.found ?
                                        <MenuItem action={this.openContainingFolder}>
                                            {PYTHON_LANG.action_open_containing_folder}
                                        </MenuItem> : ""}
                                    <MenuItem action={this.copyFileTitle}>{PYTHON_LANG.action_copy_file_title}</MenuItem>
                                    <MenuItem action={this.copyFilePath}>{PYTHON_LANG.action_copy_path}</MenuItem>
                                    {data.found ? <MenuItem action={this.renameVideo}>{PYTHON_LANG.action_rename_video}</MenuItem> : ""}
                                    <MenuItem className="red-flag" action={this.deleteVideo}>
                                        {data.found ? PYTHON_LANG.text_delete_video : PYTHON_LANG.text_delete_entry}
                                    </MenuItem>
                                </MenuPack>
                                <div><strong className="title">{data.file_title}</strong></div>
                            </div>
                        </div>
                        <div className={'filename-line' + (data.found ? "" : ' horizontal')}>
                            {data.found ? "" :
                                <div className="prepend clickable" onClick={this.deleteVideo}>
                                    <code className="text-not-found">{PYTHON_LANG.text_not_found_uppercase}</code>
                                    <code className="text-delete">{PYTHON_LANG.text_delete}</code>
                                </div>}
                            <div className={`filename ${alreadyOpened ? "already-opened" : ""}`}>
                                <code {...(data.found ? {className: "clickable"} : {})} {...(data.found ? {onClick: this.openVideo} : {})}>{data.filename}</code>
                            </div>
                        </div>
                        <div className="format horizontal">
                            <div className="prepend"><code>{data.extension}</code></div>
                            <div><strong title={data.file_size}>{data.size}</strong></div>
                            {" | "}
                            <div><code>{data.date}</code></div>
                        </div>
                        <div className="horizontal">
                            <div><strong>{PYTHON_LANG.text_video_unreadable}:</strong></div>
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
            return "";
        return (
            <div className="properties p-2">
                <div className="edit-properties clickable text-center mb-2" onClick={this.editProperties}>
                    PROPERTIES
                </div>
                {propDefs.map(def => {
                    const name = def.name;
                    const value = props.hasOwnProperty(name) ? props[name] : def.defaultValue;
                    let noValue;
                    if (def.multiple)
                        noValue = !value.length;
                    else
                        noValue = def.type === "str" && !value;
                    let printableValues = def.multiple ? value : [value];
                    return noValue ? "" : (
                        <div key={name} className={`property ${props.hasOwnProperty(name) ? "defined" : ""}`}>
                            <Collapsable title={name}>
                                {!noValue ? (printableValues.map((element, elementIndex) => (
                                    <span className="value clickable"
                                          key={elementIndex}
                                          onClick={() => this.props.onSelectPropertyValue(name, element)}>
                                        {element.toString()}
                                    </span>
                                ))) : <span className="no-value">{PYTHON_LANG.text_no_value}</span>}
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
                this.props.onInfo(formatString(PYTHON_LANG.status_opened, {path: this.props.data.filename}))
            })
            .catch(() => this.props.onInfo(formatString(PYTHON_LANG.status_unable_to_open, {path: this.props.data.filename})));
    }

    editProperties() {
        const data = this.props.data;
        Fancybox.load(
            <FormVideoEditProperties data={data} definitions={this.props.propDefs} onClose={properties => {
                python_call('set_video_properties', this.props.data.video_id, properties)
                    .then(() => this.props.onInfo(formatString(PYTHON_LANG.status_properties_updated, {path: data.filename}), true))
                    .catch(backend_error);
            }}/>
        );
    }

    confirmDeletion() {
        const filename = this.props.data.filename;
        const thumbnail_path = this.props.data.thumbnail_path;
        Fancybox.load(
            <Dialog title={PYTHON_LANG.form_title_confirm_delete_video}
                    yes={PYTHON_LANG.text_delete}
                    action={this.reallyDeleteVideo}>
                <div className="form-delete-video text-center bold">
                    {markdownToReact(PYTHON_LANG.form_head_confirm_delete_video)}
                    <div className="details overflow-auto px-2 py-1"><code id="filename">{filename}</code></div>
                    <p>
                        {this.props.data.has_thumbnail ? (
                            <img id="thumbnail" alt="No thumbnail available" src={thumbnail_path}/>
                        ) : (
                            <div className="no-thumbnail">{PYTHON_LANG.text_no_thumbnail}</div>
                        )}
                    </p>
                </div>
            </Dialog>
        );
    }

    dismissSimilarity() {
        const filename = this.props.data.filename;
        const thumbnail_path = this.props.data.thumbnail_path;
        Fancybox.load(
            <Dialog title={PYTHON_LANG.action_dismiss_similarity} yes={PYTHON_LANG.text_dismiss} action={this.reallyDismissSimilarity}>
                <div className="form-delete-video text-center bold">
                    <h2>{PYTHON_LANG.form_head_confirm_dismiss}</h2>
                    <div className="details overflow-auto px-2 py-1"><code id="filename">{filename}</code></div>
                    <p>
                        {this.props.data.has_thumbnail ? (
                            <img id="thumbnail" alt="No thumbnail available" src={thumbnail_path}/>
                        ) : (
                            <div className="no-thumbnail">{PYTHON_LANG.text_no_thumbnail}</div>
                        )}
                    </p>
                </div>
            </Dialog>
        );
    }

    resetSimilarity() {
        const filename = this.props.data.filename;
        const thumbnail_path = this.props.data.thumbnail_path;
        Fancybox.load(
            <Dialog title={PYTHON_LANG.action_reset_similarity}
                    yes={PYTHON_LANG.text_reset}
                    action={this.reallyResetSimilarity}>
                <div className="form-delete-video text-center bold">
                    {markdownToReact(PYTHON_LANG.form_content_reset_similarity)}
                    <div className="details overflow-auto px-2 py-1"><code id="filename">{filename}</code></div>
                    <p>
                        {this.props.data.has_thumbnail ? (
                            <img id="thumbnail" alt="No thumbnail available" src={thumbnail_path}/>
                        ) : (
                            <div className="no-thumbnail">{PYTHON_LANG.text_no_thumbnail}</div>
                        )}
                    </p>
                </div>
            </Dialog>
        );
    }

    deleteVideo() {
        if (this.props.data.found || this.props.confirmDeletion)
            this.confirmDeletion();
        else
            this.reallyDeleteVideo();
    }

    reallyDeleteVideo() {
        python_call('delete_video', this.props.data.video_id)
            .then(() => this.props.onInfo(formatString(PYTHON_LANG.status_video_deleted, {path: this.props.data.filename}), true))
            .catch(backend_error);
    }

    reallyDismissSimilarity() {
        python_call('dismiss_similarity', this.props.data.video_id)
            .then(() => this.props.onInfo(
                formatString(
                    PYTHON_LANG.status_video_similarity_cancelled,
                    {path: this.props.data.filename}
                ), true)
            )
            .catch(backend_error);
    }

    reallyResetSimilarity() {
        python_call('reset_similarity', this.props.data.video_id)
            .then(() => this.props.onInfo(
                formatString(
                    PYTHON_LANG.status_video_similarity_reset, {path: this.props.date.filename}
                ), true)
            )
            .catch(backend_error);
    }

    openContainingFolder() {
        python_call('open_containing_folder', this.props.data.video_id)
            .then(folder => {
                this.props.onInfo(formatString(PYTHON_LANG.status_opened_folder, {path: folder}));
            })
            .catch(backend_error);
    }

    copyMetaTitle() {
        const text = this.props.data.title;
        python_call('clipboard', text)
            .then(() => this.props.onInfo(formatString(PYTHON_LANG.status_copied_to_clipboard, {text})))
            .catch(() => this.props.onInfo(formatString(PYTHON_LANG.status_cannot_copy_meta_title, {text})));
    }

    copyFileTitle() {
        const text = this.props.data.file_title;
        python_call('clipboard', text)
            .then(() => this.props.onInfo(formatString(PYTHON_LANG.status_copied_to_clipboard, {text})))
            .catch(() => this.props.onInfo(formatString(PYTHON_LANG.status_cannot_copy_file_title, {text})));
    }

    copyFilePath() {
        python_call('clipboard_video_path', this.props.data.video_id)
            .then(() => this.props.onInfo(
                formatString(PYTHON_LANG.status_copied_to_clipboard, {text: this.props.data.filename})
            )
            .catch(() => this.props.onInfo(
                formatString(PYTHON_LANG.status_cannot_copy_file_path, {text: this.props.data.filename})
            )));
    }

    copyVideoID() {
        python_call('clipboard', this.props.data.video_id)
            .then(() => this.props.onInfo(
                formatString(PYTHON_LANG.status_copied_to_clipboard, {text: this.props.data.video_id})
            ))
            .catch(() => this.props.onInfo(
                formatString(PYTHON_LANG.status_cannot_copy_video_id, {text: this.props.data.video_id})
            ));
    }

    confirmMove(srcID, dstID) {
        python_call("set_video_moved", srcID, dstID)
            .then(() => this.props.onInfo(
                formatString(PYTHON_LANG.status_moved, {path: this.props.data.filename}), true
            ))
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
        python_call("select_directory", window.APP_STATE.latestMoveFolder)
            .then(directory => {
                if (directory) {
                    window.APP_STATE.latestMoveFolder = directory;
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
    groupDef: PropTypes.object.isRequired,
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