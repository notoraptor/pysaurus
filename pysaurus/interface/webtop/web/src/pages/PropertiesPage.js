import {ComponentController, SetInput} from "../components/SetInput.js";
import {Dialog} from "../dialogs/Dialog.js";
import {Cell} from "../components/Cell.js";
import {FormRenameProperty} from "../forms/FormRenameProperty.js";
import {python_call, backend_error} from "../utils/backend.js";
import {parsePropValString} from "../utils/functions.js";

const DEFAULT_VALUES = {
    bool: false,
    int: 0,
    float: 0.0,
    str: '',
};

function getDefaultValue(propType) {
    return DEFAULT_VALUES[propType].toString();
}

export class PropertiesPage extends React.Component {
    constructor(props) {
        // app: App
        // parameters {definitions}
        super(props);
        const definitions = this.props.parameters.definitions;
        const defaultType = 'str';
        this.state = {
            definitions: definitions,
            name: '',
            type: defaultType,
            enumeration: true,
            defaultValue: getDefaultValue(defaultType),
            multiple: false,
        };
        this.setType = this.setType.bind(this);
        this.back = this.back.bind(this);
        this.onChangeName = this.onChangeName.bind(this);
        this.onChangeType = this.onChangeType.bind(this);
        this.onChangeDefault = this.onChangeDefault.bind(this);
        this.onChangeMultiple = this.onChangeMultiple.bind(this);
        this.onChangeEnumeration = this.onChangeEnumeration.bind(this);
        this.reset = this.reset.bind(this);
        this.submit = this.submit.bind(this);
        this.deleteProperty = this.deleteProperty.bind(this);
        this.renameProperty = this.renameProperty.bind(this);
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
                                           id="prop-name"
                                           value={this.state.name}
                                           onChange={this.onChangeName}/>
                                </div>
                            </div>
                            <div className="entry">
                                <div className="label"><label htmlFor="prop-type">Type:</label></div>
                                <div className="input">
                                    <select id="prop-type"
                                            value={this.state.type}
                                            onChange={this.onChangeType}>
                                        <option value="bool">boolean</option>
                                        <option value="int">integer</option>
                                        <option value="float">floating number</option>
                                        <option value="str">text</option>
                                    </select>
                                </div>
                            </div>
                            <div className="entry">
                                <div className="label">
                                    <input type="checkbox"
                                           id="prop-multiple"
                                           checked={this.state.multiple}
                                           onChange={this.onChangeMultiple}/>
                                </div>
                                <div className="input"><label htmlFor="prop-multiple">accept many values</label></div>
                            </div>
                            <div className="entry">
                                <div className="label">
                                    <input type="checkbox"
                                           id="prop-enumeration"
                                           checked={this.state.enumeration}
                                           onChange={this.onChangeEnumeration}/>
                                </div>
                                <div className="input"><label htmlFor="prop-enumeration">Is enumeration</label></div>
                            </div>
                            {this.state.multiple && !this.state.enumeration ? '' : (
                                <div className="entry">
                                    <div className="label">
                                        <label htmlFor={'prop-default-' + this.state.type}>
                                            {this.state.enumeration ?
                                                'Enumeration values' + (this.state.multiple ? '' : ' (first is default)')
                                                : 'Default value'}
                                        </label>
                                    </div>
                                    <div className="input">{this.renderDefaultInput()}</div>
                                </div>
                            )}
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
                            <span><code>{def.type}</code> value{def.multiple ? 's' : ''}</span>
                            {def.enumeration ?
                                <span>&nbsp;in {'{'}{def.enumeration.join(', ')}{'}'}</span>
                                : ''}
                        </td>
                        <td className="default">
                            {(function () {
                                if (def.multiple) {
                                    return `{${def.defaultValue.join(', ')}}`;
                                } else if (def.type === "str") {
                                    return `"${def.defaultValue}"`;
                                } else {
                                    return def.defaultValue.toString();
                                }
                            })()}
                        </td>
                        <td className="options">
                            <div>
                                <button className="delete" onClick={() => this.deleteProperty(def.name)}>delete</button>
                            </div>
                            <div>
                                <button className="rename" onClick={() => this.renameProperty(def.name)}>rename</button>
                            </div>
                            {def.multiple ? (
                                <div>
                                    <button className="convert-to-unique"
                                            onClick={() => this.convertPropertyToUnique(def.name)}>
                                        convert to unique
                                    </button>
                                </div>
                            ) : (
                                <div>
                                    <button className="convert-to-multiple"
                                            onClick={() => this.convertPropertyToMultiple(def.name)}>
                                        convert to multiple
                                    </button>
                                </div>
                            )}
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
        );
    }

    renderDefaultInput() {
        if (this.state.enumeration) {
            const controller = new ComponentController(
                this, 'defaultValue', value => parsePropValString(this.state.type, null, value));
            return <SetInput identifier={'prop-default-' + this.state.type} controller={controller}/>;
        }
        if (this.state.type === 'bool') {
            return (
                <select className="prop-default"
                        id="prop-default-bool"
                        value={this.state.defaultValue}
                        onChange={this.onChangeDefault}>
                    <option value="false">false</option>
                    <option value="true">true</option>
                </select>
            );
        }
        return <input type={this.state.type === "int" ? "number" : "text"}
                      className="prop-default"
                      id={'prop-default-' + this.state.type}
                      onChange={this.onChangeDefault}
                      value={this.state.defaultValue}/>;
    }

    setType(value) {
        if (this.state.type !== value)
            this.setState({type: value, enumeration: false, defaultValue: getDefaultValue(value), multiple: false});
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

    onChangeMultiple(event) {
        this.setState({multiple: event.target.checked});
    }

    onChangeEnumeration(event) {
        const enumeration = event.target.checked;
        const defaultValue = enumeration ? [] : getDefaultValue(this.state.type);
        this.setState({enumeration, defaultValue});
    }

    reset() {
        this.setState(this.getDefaultInputState());
    }

    submit() {
        try {
            let definition = this.state.defaultValue;
            if (!this.state.enumeration)
                definition = parsePropValString(this.state.type, null, definition);
            python_call('add_prop_type', this.state.name, this.state.type, definition, this.state.multiple)
                .then(definitions => {
                    const state = this.getDefaultInputState();
                    state.definitions = definitions;
                    this.setState(state);
                })
                .catch(backend_error);
        } catch (exception) {
            window.alert(exception.toString());
        }
    }

    deleteProperty(name) {
        Fancybox.load(
            <Dialog title={`Delete property "${name}"?`} yes={'delete'} onClose={yes => {
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
                <Cell className="text-center" center={true} full={true}>
                    <h3>Are you sure you want to delete property "{name}"?</h3>
                </Cell>
            </Dialog>
        );
    }

    convertPropertyToUnique(name) {
        Fancybox.load(
            <Dialog title={`Convert to unique property "${name}"?`} yes={'convert to unique'} onClose={yes => {
                if (yes) {
                    python_call('convert_prop_to_unique', name)
                        .then(definitions => {
                            const state = this.getDefaultInputState();
                            state.definitions = definitions;
                            this.setState(state);
                        })
                        .catch(backend_error)
                }
            }}>
                <Cell className="text-center" center={true} full={true}>
                    <h3>Are you sure you want to convert to unique property "{name}"?</h3>
                </Cell>
            </Dialog>
        );
    }

    convertPropertyToMultiple(name) {
        Fancybox.load(
            <Dialog title={`Convert to multiple property "${name}"?`} yes={'convert to multiple'} onClose={yes => {
                if (yes) {
                    python_call('convert_prop_to_multiple', name)
                        .then(definitions => {
                            const state = this.getDefaultInputState();
                            state.definitions = definitions;
                            this.setState(state);
                        })
                        .catch(backend_error)
                }
            }}>
                <Cell className="text-center" center={true} full={true}>
                    <h3>Are you sure you want to convert to multiple property "{name}"?</h3>
                </Cell>
            </Dialog>
        );
    }

    renameProperty(name) {
        Fancybox.load(
            <FormRenameProperty title={name} onClose={newName => {
                if (newName) {
                    python_call('rename_property', name, newName)
                        .then(definitions => {
                            const state = this.getDefaultInputState();
                            state.definitions = definitions;
                            this.setState(state);
                        })
                        .catch(backend_error);
                }
            }}/>
        );
    }

    getDefaultInputState() {
        const defaultType = 'str';
        return {
            name: '',
            type: defaultType,
            enumeration: false,
            defaultValue: getDefaultValue(defaultType),
            multiple: false,
        };
    }
}
