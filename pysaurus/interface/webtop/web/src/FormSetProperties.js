import {ComponentController, SetInput} from "./SetInput.js";
import {Dialog} from "./Dialog.js";

function generatePropValChecker(propType, values) {
    switch (propType) {
        case "bool":
            return function(value) {
                if (["false", "true"].indexOf(value) < 0) {
                    window.alert(`Invalid bool value, expected: [false, true], got ${value}`);
                    return false;
                }
                return true;
            };
        case "int":
            return function(value) {
                if(isNaN(parseInt(value))) {
                    window.alert(`Unable to parse integer: ${value}`);
                    return false;
                }
                return true;
            };
        case "float":
            return function (value) {
                if (isNaN(parseFloat(value))) {
                    window.alert(`Unable to parse floating value: ${value}`);
                    return false;
                }
                return true;
            };
        case "str":
            return function(value) {return true;};
        case "enum":
            return function (value) {
                if (values.indexOf(value) < 0) {
                    window.alert(`Invalid enum value, expected: [${values.join(', ')}], got ${value}`);
                    return false;
                }
                return true;
            };
    }
}

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
        this.parsePropVal = this.parsePropVal.bind(this);
    }
    render() {
        const data = this.props.data;
        const hasThumbnail = data.hasThumbnail;
        return (
            <Dialog yes="save" no="cancel" onClose={this.onClose}>
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
                                let input = null;
                                if (def.multiple) {
                                    let possibleValues = null;
                                    switch (def.type) {
                                        case "bool":
                                            possibleValues = [false, true];
                                            break;
                                        case "enum":
                                            possibleValues = def.values;
                                            break;
                                        default:
                                            break;
                                    }
                                    const controller = new ComponentController(
                                        this, name, value => this.parsePropVal(def, value)
                                    );
                                    input = <SetInput controller={controller}
                                                      values={possibleValues}
                                                      onCheck={generatePropValChecker(def.type, possibleValues)} />;
                                } else {
                                    switch (def.type) {
                                        case "bool":
                                            input = (
                                                <select value={this.state[name]}
                                                        onChange={event => this.onChange(event, def)}>
                                                    <option value="false">false</option>
                                                    <option value="true">true</option>
                                                </select>
                                            );
                                            break;
                                        case "int":
                                            input = <input type="number"
                                                           onChange={event => this.onChange(event, def)}
                                                           value={this.state[name]}/>;
                                            break;
                                        case "enum":
                                            input = (
                                                <select value={this.state[name]} onChange={event => this.onChange(event, def)}>
                                                    {def.values.map((value, valueIndex) => <option key={valueIndex} value={value}>{value}</option>)}
                                                </select>
                                            );
                                            break;
                                        default:
                                            input = <input type="text"
                                                           onChange={event => this.onChange(event, def)}
                                                           value={this.state[name]}/>;
                                            break;
                                    }
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
        this.props.onClose(yes ? this.state: null);
    }
    onChange(event, def) {
        const value = this.parsePropVal(def, event.target.value);
        if (value !== undefined)
            this.setState({[def.name]: value});
    }
    parsePropVal(def, value) {
        const checker = generatePropValChecker(def.type, def.values);
        if (checker(value)) {
            switch (def.type) {
                case "bool":
                    return {"false": false, "true": true}[value];
                case "int":
                    return parseInt(value);
                case "float":
                    return parseFloat(value);
                default:
                    return value;
            }
        }
    }
}
