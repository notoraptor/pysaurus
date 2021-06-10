import {FIELDS_GROUP_DEF, GroupPermission, SORTED_FIELDS_AND_TITLES, STRING_FIELDS} from "../utils/constants.js";
import {Dialog} from "../dialogs/Dialog.js";

export class FormGroup extends React.Component {
    constructor(props) {
        // definition: GroupDef
        // properties: [PropDef]
        // onClose(groupDef)
        super(props);
        const properties = {};
        if (this.props.properties) {
            for (let def of this.props.properties)
                properties[`:${def.name}`] = def;
        }
        this.state = {
            field: this.props.definition.field || '',
            sorting: this.props.definition.sorting || 'field',
            reverse: this.props.definition.reverse || false,
            allowSingletons: this.props.definition.allow_singletons || true,
            allowMultiple: this.props.definition.allow_multiple || true,
            properties: properties
        };
        this.onChangeAllowSingleton = this.onChangeAllowSingleton.bind(this);
        this.onChangeAllowMultiple = this.onChangeAllowMultiple.bind(this);
        this.onChangeGroupField = this.onChangeGroupField.bind(this);
        this.onChangeSorting = this.onChangeSorting.bind(this);
        this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
        this.onClose = this.onClose.bind(this);
    }

    render() {
        return (
            <Dialog title={"Group videos:"} yes="group" action={this.onClose}>
                <table className="form-group">
                    <tbody>
                    <tr>
                        <td className="label">
                            <input type="checkbox"
                                   id="allow-singletons"
                                   checked={this.state.allowSingletons}
                                   onChange={this.onChangeAllowSingleton}/>
                        </td>
                        <td>
                            <label htmlFor="allow-singletons">Allow singletons (groups with only 1 video)</label>
                        </td>
                    </tr>
                    <tr>
                        <td className="label">
                            <input type="checkbox"
                                   id="allow-multiple"
                                   checked={this.state.allowMultiple}
                                   onChange={this.onChangeAllowMultiple}/>
                        </td>
                        <td>
                            <label htmlFor="allow-multiple">Allow multiple (groups with at least 2 videos)</label>
                        </td>
                    </tr>
                    <tr>
                        <td className="label">
                            <label htmlFor="group-field">
                                Field to group (available fields depend on if singletons or multiple groups are allowed)
                            </label>
                        </td>
                        <td>
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
                        <td>
                            <select id="group-sorting" value={this.state.sorting} onChange={this.onChangeSorting}>
                                <option value="field">Field value</option>
                                {STRING_FIELDS.hasOwnProperty(this.state.field) || this.hasStringProperty(this.state.field) ?
                                    <option value="length">Field value length</option> : ''}
                                <option value="count">Group size</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td className="label">
                            <input type='checkbox'
                                   id="group-reverse"
                                   checked={this.state.reverse}
                                   onChange={this.onChangeGroupReverse}/>
                        </td>
                        <td>
                            <label htmlFor="group-reverse">sort in reverse order</label>
                        </td>
                    </tr>
                    </tbody>
                </table>
            </Dialog>
        );
    }

    hasStringProperty(name) {
        return name.charAt(0) === ':' && this.state.properties[name].type === "str";
    }

    getDefaultField() {
        return document.querySelector('#group-field').options[0].value;
    }

    renderFieldOptions() {
        const options = [];
        let i = 0;
        if (this.props.properties) {
            for (let def of this.props.properties) {
                options.push(<option key={i} value={`:${def.name}`}>Property: {def.name}</option>);
                ++i;
            }
        }
        for (let entry of SORTED_FIELDS_AND_TITLES) {
            const [name, title] = entry;
            const permission = FIELDS_GROUP_DEF[name];
            if (
                permission === GroupPermission.ALL
                || (permission === GroupPermission.ONLY_ONE && this.state.allowSingletons && !this.state.allowMultiple)
                || (permission === GroupPermission.ONLY_MANY && !this.state.allowSingletons && this.state.allowMultiple)
            ) {
                options.push(<option key={i} value={name}>{title}</option>);
                ++i;
            }
        }
        return options;
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

    onClose() {
        this.props.onClose(Object.assign({}, this.state));
    }
}
