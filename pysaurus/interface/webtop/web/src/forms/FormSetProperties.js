import {ComponentController, SetInput} from "../components/SetInput.js";
import {Dialog} from "../dialogs/Dialog.js";
import {parsePropValString} from "../utils/functions.js";

export class FormSetProperties extends React.Component {
    constructor(props) {
        // data
        // definitions
        // onClose
        super(props);
        this.state = {};
        const properties = this.props.data.properties;
        for (let def of this.props.definitions) {
            const name = def.name;
            this.state[name] = properties.hasOwnProperty(name) ? properties[name] : def.defaultValue;
        }
        this.onClose = this.onClose.bind(this);
        this.onChange = this.onChange.bind(this);
    }

    render() {
        const data = this.props.data;
        const hasThumbnail = data.hasThumbnail;
        return (
            <Dialog title={'Edit video properties'} yes="save" onClose={this.onClose}>
                <div className="form-set-properties horizontal">
                    <div className="info">
                        <div className="image">
                            {hasThumbnail ?
                                <img alt={data.title} src={data.thumbnail_path}/> :
                                <div className="no-thumbnail">no thumbnail</div>}
                        </div>
                        <div className="filename"><code>{data.filename}</code></div>
                        {data.title === data.file_title ? '' : <div className="title"><em>{data.title}</em></div>}
                    </div>
                    <div className="properties">
                        <div className="table">
                            {this.props.definitions.map((def, index) => {
                                const name = def.name;
                                let input;
                                if (def.multiple) {
                                    let possibleValues = null;
                                    if (def.enumeration)
                                        possibleValues = def.enumeration;
                                    else if (def.type === "bool")
                                        possibleValues = [false, true];
                                    const controller = new ComponentController(
                                        this, name, value => parsePropValString(def.type, possibleValues, value));
                                    input = <SetInput controller={controller} values={possibleValues}/>;
                                } else if (def.enumeration) {
                                    input = (
                                        <select value={this.state[name]} onChange={event => this.onChange(event, def)}>
                                            {def.enumeration.map((value, valueIndex) =>
                                                <option key={valueIndex} value={value}>{value}</option>)}
                                        </select>
                                    );
                                } else if (def.type === "bool") {
                                    input = (
                                        <select value={this.state[name]}
                                                onChange={event => this.onChange(event, def)}>
                                            <option value="false">false</option>
                                            <option value="true">true</option>
                                        </select>
                                    );
                                } else {
                                    input = <input type={def.type === "int" ? "number" : "text"}
                                                   onChange={event => this.onChange(event, def)}
                                                   value={this.state[name]}/>;
                                }
                                return (
                                    <div className="table-row" key={index}>
                                        <div className="table-cell label"><strong>{name}</strong></div>
                                        <div className="table-cell input">{input}</div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </Dialog>
        );
    }

    onClose(yes) {
        this.props.onClose(yes ? this.state : null);
    }

    onChange(event, def) {
        try {
            this.setState({[def.name]: parsePropValString(def.type, def.enumeration, event.target.value)});
        } catch (exception) {
            window.alert(exception.toString());
        }
    }
}
