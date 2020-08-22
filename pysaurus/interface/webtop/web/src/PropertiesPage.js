import {SetInput, ComponentController} from "./SetInput.js";
import {Dialog} from "./Dialog.js";
import {Cell} from "./Cell.js";

const DEFAULT_VALUES = {
    bool: false,
    int: 0,
    float: 0.0,
    str: '',
    enum: ''
};

function getDefaultValue(propType) {
    if (propType === 'enum')
        return [];
    return DEFAULT_VALUES[propType];
}

export class PropertiesPage extends React.Component {
    constructor(props) {
        // app: App
        // parameters {definitons}
        super(props);
        const definitions = this.props.parameters.definitions;
        const defaultType = 'enum';
        this.state = {
            definitions: definitions,
            name: '',
            type: defaultType,
            defaultValue: getDefaultValue(defaultType),
            multiple: false,
        };
        this.setType = this.setType.bind(this);
        this.back = this.back.bind(this);
        this.onChangeName = this.onChangeName.bind(this);
        this.onChangeType = this.onChangeType.bind(this);
        this.onChangeDefault = this.onChangeDefault.bind(this);
        this.onChangeDefaultBool = this.onChangeDefaultBool.bind(this);
        this.onChangeMultiple = this.onChangeMultiple.bind(this);
        this.reset = this.reset.bind(this);
        this.submit = this.submit.bind(this);
        this.deleteProperty = this.deleteProperty.bind(this);
        this.getDefaultInputState = this.getDefaultInputState.bind(this);
    }

    render() {
        return (
            <div id="properties">
                <h2 className="horizontal">
                    <div className="back">
                        <button onClick={this.back}>&#11164;</button>
                    </div>
                    <div className="title">Properties Management</div>
                </h2>
                <hr/>
                <div className="content horizontal">
                    <div className="list">
                        <h3>Current properties</h3>
                        {this.renderPropTypes()}
                    </div>
                    <div className="new">
                        <h3>Add a new property</h3>
                        <div className="entries">
                            <div className="entry">
                                <div className="label"><label htmlFor="prop-name">Name:</label></div>
                                <div className="input">
                                    <input type="text"
                                           name="name"
                                           id="prop-name"
                                           value={this.state.name}
                                           onChange={this.onChangeName}/>
                                </div>
                            </div>
                            <div className="entry">
                                <div className="label"><label htmlFor="prop-type">Type:</label></div>
                                <div className="input">
                                    <select name="type"
                                            id="prop-type"
                                            value={this.state.type}
                                            onChange={this.onChangeType}>
                                        <option value="bool">boolean</option>
                                        <option value="int">integer</option>
                                        <option value="float">floating number</option>
                                        <option value="str">text</option>
                                        <option value="enum">enumeration</option>
                                    </select>
                                </div>
                            </div>
                            <div className="entry">
                                <div className="label">
                                    <label htmlFor={'prop-default-' + this.state.type}>
                                        {this.state.type === 'enum' ?
                                            'Enumeration values (first is default)'
                                            : 'Default value'}
                                    </label>
                                </div>
                                <div className="input">
                                    {this.renderDefaultInput()}
                                </div>
                            </div>
                            <div className="entry">
                                <div className="label">
                                    <input type="checkbox"
                                           name="multiple"
                                           id="prop-multiple"
                                           checked={this.state.multiple}
                                           onChange={this.onChangeMultiple}/>
                                </div>
                                <div className="input">
                                    <label htmlFor="prop-multiple">accept many values</label>
                                </div>
                            </div>
                            <div className="entry buttons">
                                <div className="label">
                                    <button className="reset" onClick={this.reset}>reset</button>
                                </div>
                                <div className="input">
                                    <button className="submit" onClick={this.submit}>add</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
    renderPropTypes() {
        return (
            <table>
                <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Default</th>
                    <th>Options</th>
                </tr>
                </thead>
                <tbody>
                {this.state.definitions.map((def, index) => (
                    <tr key={index}>
                        <td className="name">{def.name}</td>
                        <td className="type">
                            {def.multiple ? <span>one or many&nbsp;</span> : ''}
                            {def.type === 'enum' ?
                                <span>
                                    value{def.multiple ? 's' : ''} in {'{'}{def.values.join(', ')}{'}'}
                                </span>
                                : <span>{def.type}</span>}
                        </td>
                        <td className="default">
                            {['str', 'enum'].indexOf(def.type) >= 0 ? '"' : ''}
                            {def.defaultValue.toString()}
                            {['str', 'enum'].indexOf(def.type) >= 0 ? '"' : ''}
                        </td>
                        <td className="options">
                            <button className="delete" onClick={() => this.deleteProperty(def.name)}>delete</button>
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
        );
    }
    renderDefaultInput() {
        if (this.state.type === 'bool') {
            return (
                <select className="prop-default"
                        id="prop-default-bool"
                        value={this.state.defaultValue}
                        onChange={this.onChangeDefaultBool}>
                    <option value="false">false</option>
                    <option value="true">true</option>
                </select>
            );
        }
        if (this.state.type === 'int') {
            return <input type="number"
                          className="prop-default"
                          id="prop-default-int"
                          onChange={this.onChangeDefault}
                          value={this.state.defaultValue}/>;
        }
        if (this.state.type === 'enum') {
            const controller = new ComponentController(this, 'defaultValue');
            return <SetInput identifier={'prop-default-' + this.state.type} controller={controller}/>;
        }
        return <input type="text"
                      className="prop-default"
                      id={'prop-default-' + this.state.type}
                      onChange={this.onChangeDefault}
                      value={this.state.defaultValue}/>;
    }

    setType(value) {
        if (this.state.type !== value)
            this.setState({type: value, defaultValue: getDefaultValue(value)});
    }
    back() {
        this.props.app.loadVideosPage();
    }
    onChangeName(event) {
        const name = event.target.value;
        if (this.state.name !== name)
            this.setState({name});
    }
    onChangeType(event) {
        this.setType(event.target.value);
    }
    onChangeDefault(event) {
        const defaultValue = event.target.value;
        if (this.state.defaultValue !== defaultValue)
            this.setState({defaultValue});
    }
    onChangeDefaultBool(event) {
        const defaultValue = {"true": true, "false": false}[event.target.value];
        if (this.state.defaultValue !== defaultValue)
            this.setState({defaultValue});
    }
    onChangeMultiple(event) {
        this.setState({multiple: event.target.checked});
    }
    reset() {
        this.setState(this.getDefaultInputState());
    }
    submit() {
        python_call('add_prop_type', this.state.name, this.state.type, this.state.defaultValue, this.state.multiple)
            .then(definitions => {
                const state = this.getDefaultInputState();
                state.definitions = definitions;
                this.setState(state);
            })
            .catch(backend_error);
    }
    deleteProperty(name) {
        this.props.app.loadDialog(`Delete property "${name}"?`, onClose => (
            <Dialog yes={'delete'} no={'cancel'} onClose={yes => {
                onClose();
                if (yes) {
                    python_call('delete_prop_type', name)
                        .catch(backend_error)
                        .then(definitions => {
                            const state = this.getDefaultInputState();
                            state.definitions = definitions;
                            this.setState(state);
                        })
                }
            }}>
                <Cell className="delete-property" center={true} full={true}>
                    <h3>Are you sure you want to delete property "{name}"?</h3>
                </Cell>
            </Dialog>
        ));
    }
    getDefaultInputState() {
        const defaultType = 'str';
        return {
            name: '',
            type: defaultType,
            defaultValue: getDefaultValue(defaultType),
            multiple: false,
        };
    }
}