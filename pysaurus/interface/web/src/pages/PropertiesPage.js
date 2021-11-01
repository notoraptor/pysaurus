import {ComponentPropController, SetInput} from "../components/SetInput.js";
import {Dialog} from "../dialogs/Dialog.js";
import {Cell} from "../components/Cell.js";
import {FormPropertyRename} from "../forms/FormPropertyRename.js";
import {backend_error, python_call} from "../utils/backend.js";
import {LangContext} from "../language.js";
import {utilities} from "../utils/functions.js";

const DEFAULT_VALUES = {
    bool: false,
    int: 0,
    float: 0.0,
    str: "",
};

function getDefaultValue(propType, isEnum) {
    return isEnum ? [] : DEFAULT_VALUES[propType].toString();
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
            name: "",
            type: defaultType,
            enumeration: true,
            defaultValue: getDefaultValue(defaultType, true),
            multiple: false,
        };
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
                <h2 className="horizontal ml-1 mr-1">
                    <div className="back position-relative">
                        <button className="block bold h-100 px-4" onClick={this.back}>&#11164;</button>
                    </div>
                    <div className="text-center flex-grow-1">{this.context.gui_properties_title}</div>
                </h2>
                <hr/>
                <div className="content horizontal">
                    <div className="list text-center">
                        <h3 className="text-center">{this.context.gui_properties_current}</h3>
                        {this.renderPropTypes()}
                    </div>
                    <div className="new">
                        <h3 className="text-center">{this.context.gui_properties_add_new}</h3>
                        <table className="first-td-text-right w-100">
                            <tr>
                                <td><label htmlFor="prop-name">Name:</label></td>
                                <td>
                                    <input type="text"
                                           id="prop-name"
                                           className="block"
                                           value={this.state.name}
                                           onChange={this.onChangeName}/>
                                </td>
                            </tr>
                            <tr>
                                <td><label htmlFor="prop-type">Type:</label></td>
                                <td>
                                    <select id="prop-type"
                                            className="block"
                                            value={this.state.type}
                                            onChange={this.onChangeType}>
                                        <option value="bool">{this.context.text_boolean}</option>
                                        <option value="int">{this.context.text_integer}</option>
                                        <option value="float">{this.context.text_float}</option>
                                        <option value="str">{this.context.text_text}</option>
                                    </select>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <input type="checkbox"
                                           id="prop-multiple"
                                           checked={this.state.multiple}
                                           onChange={this.onChangeMultiple}/>
                                </td>
                                <td><label htmlFor="prop-multiple">{this.context.text_accept_many_values}</label></td>
                            </tr>
                            <tr>
                                <td>
                                    <input type="checkbox"
                                           id="prop-enumeration"
                                           checked={this.state.enumeration}
                                           onChange={this.onChangeEnumeration}/>
                                </td>
                                <td><label htmlFor="prop-enumeration">{this.context.text_is_enumeration}</label></td>
                            </tr>
                            {!this.state.multiple || this.state.enumeration ? (
                                <tr>
                                    <td>
                                        <label htmlFor={'prop-default-' + this.state.type}>
                                            {this.state.enumeration ? (
                                                this.state.multiple ?
                                                    this.context.gui_properties_enumeration_values_multiple :
                                                    this.context.gui_properties_enumeration_values
                                            ) : this.context.gui_properties_default_value}
                                        </label>
                                    </td>
                                    <td>{this.renderDefaultInput()}</td>
                                </tr>
                            ) : ""}
                            <tr className="buttons">
                                <td>
                                    <button className="reset block" onClick={this.reset}>reset</button>
                                </td>
                                <td>
                                    <button className="submit bold block" onClick={this.submit}>add</button>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        );
    }

    renderPropTypes() {
        return (
            <table className="w-100">
                <thead className="bold">
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
                        <td className="name bold">{def.name}</td>
                        <td className="type">
                            {def.multiple ? <span>{this.context.text_one_or_many}&nbsp;</span> : ""}
                            <span><code>{def.type}</code> {def.multiple ? this.context.word_values : this.context.word_value}</span>
                            {def.enumeration ?
                                <span>&nbsp;{this.context.word_in} {'{'}{def.enumeration.join(', ')}{'}'}</span>
                                : ""}
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
                                <button className="delete red-flag"
                                        onClick={() => this.deleteProperty(def.name)}>delete
                                </button>
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
            const controller = new ComponentPropController(this, 'defaultValue', this.state.type, null);
            return <SetInput className="block" identifier={'prop-default-' + this.state.type} controller={controller}/>;
        }
        if (this.state.type === 'bool') {
            return (
                <select className="prop-default block"
                        id="prop-default-bool"
                        value={this.state.defaultValue}
                        onChange={this.onChangeDefault}>
                    <option value="false">false</option>
                    <option value="true">true</option>
                </select>
            );
        }
        return <input type={this.state.type === "int" ? "number" : "text"}
                      className="prop-default block"
                      id={'prop-default-' + this.state.type}
                      onChange={this.onChangeDefault}
                      value={this.state.defaultValue}/>;
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
        const value = event.target.value;
        if (this.state.type !== value)
            this.setState({type: value, enumeration: false, defaultValue: getDefaultValue(value), multiple: false});
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
        const defaultValue = getDefaultValue(this.state.type, enumeration);
        this.setState({enumeration, defaultValue});
    }

    reset() {
        this.setState(this.getDefaultInputState());
    }

    submit() {
        try {
            let definition = this.state.defaultValue;
            if (!this.state.enumeration)
                definition = utilities(this.context).parsePropValString(this.state.type, null, definition);
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
            <Dialog title={this.context.form_title_delete_property.format({name})} yes={this.context.text_delete} action={() => {
                python_call('delete_prop_type', name)
                    .catch(backend_error)
                    .then(definitions => {
                        const state = this.getDefaultInputState();
                        state.definitions = definitions;
                        this.setState(state);
                    })
            }}>
                <Cell className="text-center" center={true} full={true}>
                    <h3>{this.context.form_content_delete_property.format({name})}</h3>
                </Cell>
            </Dialog>
        );
    }

    convertPropertyToUnique(name) {
        Fancybox.load(
            <Dialog title={this.context.form_title_convert_to_unique_property.format({name})}
                    yes={this.context.form_convert_to_unique_property_yes}
                    action={() => {
                python_call('convert_prop_to_unique', name)
                    .then(definitions => {
                        const state = this.getDefaultInputState();
                        state.definitions = definitions;
                        this.setState(state);
                    })
                    .catch(backend_error)
            }}>
                <Cell className="text-center" center={true} full={true}>
                    <h3>{this.context.form_confirm_convert_to_unique_property.format({name})}</h3>
                </Cell>
            </Dialog>
        );
    }

    convertPropertyToMultiple(name) {
        Fancybox.load(
            <Dialog title={this.context.form_title_convert_to_multiple_property.format({name})}
                    yes={this.context.form_convert_to_multiple_property_yes}
                    action={() => {
                python_call('convert_prop_to_multiple', name)
                    .then(definitions => {
                        const state = this.getDefaultInputState();
                        state.definitions = definitions;
                        this.setState(state);
                    })
                    .catch(backend_error)
            }}>
                <Cell className="text-center" center={true} full={true}>
                    <h3>{this.context.form_confirm_convert_to_multiple_property.format({name})}</h3>
                </Cell>
            </Dialog>
        );
    }

    renameProperty(name) {
        Fancybox.load(
            <FormPropertyRename title={name} onClose={newName => {
                python_call('rename_property', name, newName)
                    .then(definitions => {
                        const state = this.getDefaultInputState();
                        state.definitions = definitions;
                        this.setState(state);
                    })
                    .catch(backend_error);
            }}/>
        );
    }

    getDefaultInputState() {
        const defaultType = 'str';
        return {
            name: "",
            type: defaultType,
            enumeration: false,
            defaultValue: getDefaultValue(defaultType),
            multiple: false,
        };
    }
}
PropertiesPage.contextType = LangContext;
