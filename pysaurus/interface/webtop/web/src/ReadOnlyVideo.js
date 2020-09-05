import {MenuPack, MenuItem} from "./MenuPack.js";
import {FormRenameVideo} from "./FormRenameVideo.js";
import {Dialog} from "./Dialog.js";
import {FormSetProperties} from "./FormSetProperties.js";

export class ReadOnlyVideo extends React.Component {
    constructor(props) {
        // index
        // data
        // propDefs
        super(props);
        this.openVideo = this.openVideo.bind(this);
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
        const hasThumbnail = data.hasThumbnail;
        return (
            <div className={'video horizontal' + (index % 2 ? ' even' : ' odd') + (data.exists ? ' found' : ' not-found')}>
                <div className="image">
                    {hasThumbnail ?
                        <img alt={data.title} src={data.thumbnail_path}/> :
                        <div className="no-thumbnail">no thumbnail</div>}
                </div>
                <div className="info">
                    <div className="name">
                        <strong className="title">{data.title}</strong>
                        {data.title === data.file_title ? '' : <div className="file-title"><em>{data.file_title}</em></div>}
                    </div>
                    <div className={'filename-line' + (data.exists ? '' : ' horizontal')}>
                        <div className="filename"><code {...(data.exists ? {onClick: this.openVideo} : {})}>{data.filename}</code></div>
                    </div>
                    <div className="format horizontal">
                        <div className="prepend"><code>{data.extension}</code></div>
                        <div><strong title={data.file_size}>{data.size}</strong> / {data.container_format} (<span title={data.video_codec_description}>{data.video_codec}</span>, <span title={data.audio_codec_description}>{data.audio_codec}</span>)</div>
                        <div className="prepend"><code>Quality</code></div>
                        <div><strong><em>{data.quality}</em></strong> %</div>
                    </div>
                    <div><strong>{data.width}</strong> x <strong>{data.height}</strong> @ {data.frame_rate} fps | {data.sample_rate} Hz, <span title={data.audio_bit_rate}>{audio_bit_rate} Kb/s</span> | <strong>{data.length}</strong> | <code>{data.date}</code></div>
                    {this.renderProperties()}
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
            <div className="properties">
                <div className="table">
                    {propDefs.map((def, index) => {
                        const name = def.name;
                        const value = props.hasOwnProperty(name) ? props[name] : def.defaultValue;
                        const valueString = propertyValueToString(def.type,def.multiple ? value.join(', ') : value.toString());
                        return (
                            <div key={name} className="property table-row">
                                <div className="table-cell property-name"><strong {...(props.hasOwnProperty(name) ? {className: "defined"} : {})}>{name}</strong>:</div>
                                <div className="table-cell">
                                    {valueString ? <span>{valueString}</span> : <span className="no-value">no value</span>}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    }
    openVideo() {
        python_call('open_video_from_filename', this.props.data.filename)
            .then(result => {
                if (result)
                    this.props.parent.updateStatus('Opened: ' + this.props.data.filename);
                else
                    this.props.parent.updateStatus('Unable to open: ' + this.props.data.filename);
            })
            .catch(backend_error);
    }
}
