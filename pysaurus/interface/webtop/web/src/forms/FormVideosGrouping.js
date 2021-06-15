import {FIELD_MAP} from "../utils/constants.js";
import {Dialog} from "../dialogs/Dialog.js";

export class FormVideosGrouping extends React.Component {
    constructor(props) {
        // groupDef: GroupDef
        // properties: [PropDef]
        // propertyMap: {name: PropDef}
        // onClose(groupDef)
        super(props);
        this.state = this.props.groupDef.field ? {
            isProperty: this.props.groupDef.is_property,
            field: this.props.groupDef.field,
            sorting: this.props.groupDef.sorting,
            reverse: this.props.groupDef.reverse,
            allowSingletons: this.props.groupDef.allow_singletons,
        } : {
            isProperty: false,
            field: FIELD_MAP.list[0].name,
            sorting: "field",
            reverse: false,
            allowSingletons: !FIELD_MAP.list[0].isOnlyMany(),
        };
        this.onChangeAllowSingletons = this.onChangeAllowSingletons.bind(this);
        this.onChangeGroupField = this.onChangeGroupField.bind(this);
        this.onChangeSorting = this.onChangeSorting.bind(this);
        this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
        this.onClose = this.onClose.bind(this);
        this.onChangeFieldType = this.onChangeFieldType.bind(this);
    }

    render() {
        return (
            <Dialog title={"Group videos:"} yes="group" action={this.onClose}>
                <table className="form-group">
                    <tbody>
                    <tr>
                        <td className="label">Field type</td>
                        <td>
                            <input id="field-type-property"
                                   type="radio"
                                   value="true"
                                   checked={this.state.isProperty}
                                   onChange={this.onChangeFieldType}/>
                            {" "}
                            <label htmlFor="field-type-property">property</label>
                            {" "}
                            <input id="field-type-attribute"
                                   type="radio"
                                   value="false"
                                   checked={!this.state.isProperty}
                                   onChange={this.onChangeFieldType}/>
                            {" "}
                            <label htmlFor="field-type-attribute">attribute</label>
                        </td>
                    </tr>
                    <tr>
                        <td className="label"><label htmlFor="group-field">Field</label></td>
                        <td>
                            <select id="group-field" value={this.state.field} onChange={this.onChangeGroupField}>
                                {this.state.isProperty ? (
                                    this.props.properties.map((def, index) => (
                                        <option key={index} value={def.name}>{def.name}</option>
                                    ))
                                ) : (
                                    FIELD_MAP.list.map((fieldOption, index) => (
                                        <option key={index} value={fieldOption.name}>{fieldOption.title}</option>
                                    ))
                                )}
                            </select>
                        </td>
                    </tr>
                    {this.state.isProperty || !FIELD_MAP.fields[this.state.field].isOnlyMany() ? (
                        <tr>
                            <td className="label">
                                <input type="checkbox"
                                       id="allow-singletons"
                                       checked={this.state.allowSingletons}
                                       onChange={this.onChangeAllowSingletons}/>
                            </td>
                            <td>
                                <label htmlFor="allow-singletons">Allow singletons (groups with only 1 video)</label>
                            </td>
                        </tr>
                    ) : ''}
                    <tr>
                        <td className="label">
                            <label htmlFor="group-sorting">Sort using:</label>
                        </td>
                        <td>
                            <select id="group-sorting" value={this.state.sorting} onChange={this.onChangeSorting}>
                                <option value="field">Field value</option>
                                {this.fieldIsString() ? <option value="length">Field value length</option> : ''}
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

    fieldIsString() {
        if (this.state.isProperty)
            return this.props.propertyMap[this.state.field].type === "str";
        return FIELD_MAP.fields[this.state.field].isString;
    }

    onChangeFieldType(event) {
        const isProperty = event.target.value === "true";
        const field = isProperty ? this.props.properties[0].name : FIELD_MAP.list[0].name;
        const sorting = "field";
        const reverse = false;
        const allowSingletons = isProperty || !FIELD_MAP.list[0].isOnlyMany();
        this.setState({isProperty, field, sorting, reverse, allowSingletons});
    }

    onChangeGroupField(event) {
        const field = event.target.value;
        const sorting = "field";
        const reverse = false;
        const allowSingletons = this.state.isProperty || !FIELD_MAP.fields[field].isOnlyMany();
        this.setState({field, sorting, reverse, allowSingletons});
    }

    onChangeAllowSingletons(event) {
        this.setState({allowSingletons: event.target.checked});
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
