import {FIELDS_GROUP_DEF, GroupPermission, SORTED_FIELDS_AND_TITLES, STRING_FIELDS} from "./constants.js";
import {Dialog} from "./Dialog.js";


const REVERSE_VALUES = {"true": true, "false": false};

export class FormGroup extends React.Component {
    constructor(props) {
        // definition: GroupDef
        // onClose(groupDef)
        super(props);
        this.state = {
            field: this.props.definition.field || '',
            sorting: this.props.definition.sorting || 'field',
            reverse: this.props.definition.reverse || false,
            allowSingletons: this.props.definition.allowSingletons || false,
            allowMultiple: this.props.definition.allowMultiple || true,
        };
        this.onChangeAllowSingleton = this.onChangeAllowSingleton.bind(this);
        this.onChangeAllowMultiple = this.onChangeAllowMultiple.bind(this);
        this.onChangeGroupField = this.onChangeGroupField.bind(this);
        this.onChangeSorting = this.onChangeSorting.bind(this);
        this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
        this.onClose = this.onClose.bind(this);
    }
    getDefaultField() {
        return document.querySelector('#group-field').options[0].value;
    }
    renderFieldOptions() {
        const options = [];
        for (let i = 0; i < SORTED_FIELDS_AND_TITLES.length; ++i) {
            const [name, title] = SORTED_FIELDS_AND_TITLES[i];
            const permission = FIELDS_GROUP_DEF[name];
            if (
                permission === GroupPermission.ALL
                || (permission === GroupPermission.ONLY_ONE && this.state.allowSingletons && !this.state.allowMultiple)
                || (permission === GroupPermission.ONLY_MANY && !this.state.allowSingletons && this.state.allowMultiple)
            ) {
                options.push(<option key={i} value={name}>{title}</option>);
            }
        }
        return options;
    }
    render() {
        return (
            <Dialog yes="group" no="cancel" onClose={this.onClose}>
                <table className="form-group">
                    <tbody>
                        <tr>
                            <td className="label">
                                <input type="checkbox" id="allow-singletons" checked={this.state.allowSingletons} onChange={this.onChangeAllowSingleton}/>
                            </td>
                            <td className="input">
                                <label htmlFor="allow-singletons">Allow singletons (groups with only 1 video)</label>
                            </td>
                        </tr>
                        <tr>
                            <td className="label">
                                <input type="checkbox" id="allow-multiple" checked={this.state.allowMultiple} onChange={this.onChangeAllowMultiple}/>
                            </td>
                            <td className="input">
                                <label htmlFor="allow-multiple">Allow multiple (groups with at least 2 videos)</label>
                            </td>
                        </tr>
                        <tr>
                            <td className="label">
                                <label htmlFor="group-field">
                                    Field to group (available fields depend on if singletons or multiple groups are allowed)
                                </label>
                            </td>
                            <td className="input">
                                <select id="group-field"
                                        value={this.state.field}
                                        onChange={this.onChangeGroupField}>
                                    {this.renderFieldOptions()}
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td className="label">
                                <label htmlFor="group-sorting">Sort using:</label>
                            </td>
                            <td className="input">
                                <select id="group-sorting" value={this.state.sorting} onChange={this.onChangeSorting}>
                                    <option value="field">Field value</option>
                                    {STRING_FIELDS.hasOwnProperty(this.state.field) ? <option value="length">Field value length</option> : ''}
                                    <option value="count">Group size</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td className="label">
                                <input type='checkbox' id="group-reverse" checked={this.state.reverse} onChange={this.onChangeGroupReverse}/>
                            </td>
                            <td className="input">
                                <label htmlFor="group-reverse">sort in reverse order</label>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </Dialog>
        );
    }
    componentDidMount() {
        if (!this.state.field)
            this.setState({field: this.getDefaultField()});
    }
    onChangeAllowSingleton(event) {
        this.setState({
            allowSingletons: event.target.checked,
            field: this.getDefaultField(),
            sorting: "field",
            reverse: false
        });
    }
    onChangeAllowMultiple(event) {
        this.setState({
            allowMultiple: event.target.checked,
            field: this.getDefaultField(),
            sorting: "field",
            reverse: false
        });
    }
    onChangeGroupField(event) {
        this.setState({field: event.target.value, sorting: 'field', reverse: false});
    }
    onChangeSorting(event) {
        this.setState({sorting: event.target.value, reverse: false});
    }
    onChangeGroupReverse(event) {
        this.setState({reverse: event.target.checked});
    }
    onClose(yes) {
        let definition = null;
        if (yes) {
            definition = Object.assign({}, this.state);
        }
        this.props.onClose(definition);
    }
}