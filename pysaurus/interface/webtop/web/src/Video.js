import {MenuPack, MenuItem} from "./MenuPack.js";
import {FormRenameVideo} from "./FormRenameVideo.js";
import {Dialog} from "./Dialog.js";
import {FormSetProperties} from "./FormSetProperties.js";

export class Video extends React.Component {
    constructor(props) {
        // parent
        // index
        // data
        // confirmDeletion: bool
        super(props);
        this.openVideo = this.openVideo.bind(this);
        this.confirmDeletion = this.confirmDeletion.bind(this);
        this.deleteVideo = this.deleteVideo.bind(this);
        this.openContainingFolder = this.openContainingFolder.bind(this);
        this.copyMetaTitle = this.copyMetaTitle.bind(this);
        this.copyFileTitle = this.copyFileTitle.bind(this);
        this.renameVideo = this.renameVideo.bind(this);
        this.editProperties = this.editProperties.bind(this);
    }
    render() {
        const index = this.props.index;
        const data = this.props.data;
        const audio_bit_rate = Math.round(data.audio_bit_rate / 1000);
        data.extension = data.extension.toUpperCase();
        data.frame_rate = Math.round(data.frame_rate);
        data.quality = Math.round(data.quality * 100) / 100;
        const title = data.title;
        const file_title = data.file_title;
        const meta_title = (title === file_title ? null : title);
        const hasThumbnail = data.hasThumbnail;
        return (
            <div className={'video horizontal' + (data.exists ? ' found' : ' not-found')}>
                <div className="image">
                    {hasThumbnail ?
                        <img alt={data.title} src={data.thumbnail_path}/> :
                        <div className="no-thumbnail">no thumbnail</div>}
                </div>
                <div className="info">
                    <div className="name">
                        <div className="options horizontal">
                            <MenuPack title={`${Utils.CHARACTER_SETTINGS}`}>
                                {data.exists ? <MenuItem action={this.openVideo}>Open file</MenuItem> : <div className="not-found">(not found)</div>}
                                {data.exists ? <MenuItem action={this.openContainingFolder}>Open containing folder</MenuItem> : ''}
                                {meta_title ? <MenuItem action={this.copyMetaTitle}>Copy meta title</MenuItem> : ''}
                                {file_title ? <MenuItem action={this.copyFileTitle}>Copy file title</MenuItem> : ''}
                                {data.exists && this.props.parent.state.properties.length ?
                                    <MenuItem action={this.editProperties}>Edit properties ...</MenuItem> : ''}
                                {data.exists ? <MenuItem action={this.renameVideo}>Rename video</MenuItem> : ''}
                                <MenuItem className="menu-delete" action={this.deleteVideo}>{data.exists ? 'Delete video' : 'Delete entry'}</MenuItem>
                            </MenuPack>
                            <strong className="title">{data.title}</strong>
                        </div>
                        {data.title === data.file_title ? '' : <div className="file-title"><em>{data.file_title}</em></div>}
                    </div>
                    <div className={'filename-line' + (data.exists ? '' : ' horizontal')}>
                        {data.exists ? '' : <div className="prepend" onClick={this.deleteVideo}><code className="text-not-found">NOT FOUND</code><code className="text-delete">DELETE</code></div>}
                        <div className="filename"><code {...(data.exists ? {onClick: this.openVideo} : {})}>{data.filename}</code></div>
                    </div>
                    <div className="format horizontal">
                        <div className="prepend"><code>{data.extension}</code></div>
                        <div><strong title={data.file_size}>{data.size}</strong> / {data.container_format} (<span title={data.video_codec_description}>{data.video_codec}</span>, <span title={data.audio_codec_description}>{data.audio_codec}</span>)</div>
                        <div className="prepend"><code>Quality</code></div>
                        <div><strong><em>{data.quality}</em></strong> %</div>
                    </div>
                    <div><strong>{data.width}</strong> x <strong>{data.height}</strong> @ {data.frame_rate} fps | {data.sample_rate} Hz, <span title={data.audio_bit_rate}>{audio_bit_rate} Kb/s</span> | <strong>{data.length}</strong> | <code>{data.date}</code></div>
                </div>
                {this.renderProperties()}
            </div>
        );
    }
    renderProperties() {
        const props = this.props.data.properties;
        const propDefs = this.props.parent.state.properties;
        if (!propDefs.length)
            return '';
        return (
            <div className="properties">
                <div className="table">
                {propDefs.map((def, index) => {
                    const name = def.name;
                    const value = props.hasOwnProperty(name) ? props[name] : def.defaultValue;
                    const valueString = propertyValueToString(def.type,def.multiple ? value.join(', ') : value.toString());
                    let noValue;
                    if (def.multiple)
                        noValue = !value.length;
                    else
                        noValue = def.type === "str" && !value;
                    let printableValues = def.multiple ? value : [value];
                    let tooMuch = false;
                    if (printableValues.length > 10) {
                        tooMuch = true;
                        printableValues = printableValues.slice(0, 10);
                    }
                    return (
                        <div key={name} className="property table-row">
                            <div className="table-cell property-name"><strong {...(props.hasOwnProperty(name) ? {className: "defined"} : {})}>{name}</strong>:</div>
                            <div className="table-cell property-value">
                                {!noValue ? (printableValues.map((element, elementIndex) => (
                                    <span className="value" key={elementIndex}>{element.toString()}</span>
                                ))) : <span className="no-value">no value</span>}
                                {tooMuch ? ' ...' : ''}
                            </div>
                        </div>
                    );
                })}
                </div>
            </div>
        );
    }
    openVideo() {
        python_call('open_video', this.props.index)
            .then(result => {
                if (result)
                    this.props.parent.updateStatus('Opened: ' + this.props.data.filename);
                else
                    this.props.parent.updateStatus('Unable to open: ' + this.props.data.filename);
            })
            .catch(backend_error);
    }
    editProperties() {
        const data = this.props.data;
        const definitions = this.props.parent.state.properties;
        this.props.parent.props.app.loadDialog('Edit video properties', onClose => (
            <FormSetProperties data={data} definitions={definitions} onClose={properties => {
                onClose();
                if (properties) {
                    python_call('set_video_properties', this.props.index, properties)
                        .then(() => this.props.parent.updateStatus(`Properties updated: ${data.filename}`, true))
                        .catch(backend_error);
                }
            }} />
        ));
    }
    confirmDeletion() {
        /*
        return view.dialog({
            url: 'html/delete.html',
            parameters: {filename: this.props.data.filename, thumbnail_path: this.props.data.thumbnail_path}}
        );
        */
        const filename = this.props.data.filename;
        const thumbnail_path = this.props.data.thumbnail_path;
        this.props.parent.props.app.loadDialog('Confirm deletion', onClose => (
            <Dialog yes="delete" no="cancel" onClose={yes => {
                onClose();
                if (yes)
                    this.reallyDeleteVideo();
            }}>
                <div className="form-delete-video">
                    <h2>Are you sure you want to <strong>definitely</strong> delete this video?</h2>
                    <div className="details"><code id="filename">{filename}</code></div>
                    <p><img id="thumbnail" alt="No thumbnail available" src={thumbnail_path}/></p>
                </div>
            </Dialog>
        ));
    }
    deleteVideo() {
        if (this.props.data.exists || this.props.confirmDeletion)
            this.confirmDeletion();
        else
            this.reallyDeleteVideo();
    }
    reallyDeleteVideo() {
        python_call('delete_video', this.props.index)
            .then(result => {
                if (result)
                    this.props.parent.updateStatus('Video deleted! ' + this.props.data.filename, true);
                else
                    this.props.parent.updateStatus('Unable to delete video! ' + this.props.data.filename, true);
            })
            .catch(backend_error);
    }
    openContainingFolder() {
        python_call('open_containing_folder', this.props.index)
            .then(folder => {
                if (folder)
                    this.props.parent.updateStatus('Opened folder: ' + folder);
                else
                    this.props.parent.updateStatus('Unable to open containing folder for: ' + this.props.data.filename);
            })
            .catch(backend_error);
    }
    copyMetaTitle() {
        const text = this.props.data.title;
        python_call('clipboard', text)
            .then(() => this.props.parent.updateStatus('Copied to clipboard: ' + text))
            .catch(() => this.props.parent.updateStatus(`Cannot copy meta title to clipboard: ${text}`));
    }
    copyFileTitle() {
        const text = this.props.data.file_title;
        python_call('clipboard', text)
            .then(() => this.props.parent.updateStatus('Copied to clipboard: ' + text))
            .catch(() => this.props.parent.updateStatus(`Cannot copy file title to clipboard: ${text}`));
    }
    renameVideo() {
        const filename = this.props.data.filename;
        const title = this.props.data.file_title;
        this.props.parent.props.app.loadDialog('Rename', onClose => (
            <FormRenameVideo filename={filename} title={title} onClose={newTitle => {
                onClose();
                if (newTitle) {
                    python_call('rename_video', this.props.index, newTitle)
                        .then(() => {
                            this.props.parent.updateStatus(`Renamed: ${newTitle}`, true)
                        })
                        .catch(backend_error);
                }
            }}/>
        ));
    }
}
