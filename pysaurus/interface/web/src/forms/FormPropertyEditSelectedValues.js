import {Dialog} from "../dialogs/Dialog.js";
import {formatString, parsePropValString} from "../utils/functions.js";

export class FormPropertyEditSelectedValues extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            form: 'edit',
            value: this.props.values[0].toString(),
            move: "",
            otherDefinitions: this.getCompatibleDefinitions()
        };
        this.setDelete = this.setDelete.bind(this);
        this.setEdit = this.setEdit.bind(this);
        this.setMove = this.setMove.bind(this);
        this.onEdit = this.onEdit.bind(this);
        this.onMove = this.onMove.bind(this);
        this.onClose = this.onClose.bind(this);
        this.onEditKeyDown = this.onEditKeyDown.bind(this);
        this.valuesToString = this.valuesToString.bind(this);
    }

    render() {
        const canMove = this.state.otherDefinitions.length && this.props.values.length === 1;
        const values = this.props.values;
        let title;
        if (values.length === 1)
            title = formatString(PYTHON_LANG.form_title_edit_prop_val, {name: this.props.name, value: values[0]});
        else
            title = formatString(PYTHON_LANG.form_title_edit_prop_vals, {name: this.props.name, count: values.length});
        return (
            <Dialog title={title} yes={this.state.form} action={this.onClose}>
                <div className="form-property-edit-selected-values vertical flex-grow-1">
                    <div className="bar flex-shrink-0 text-center">
                        <button className={`delete ${this.state.form === 'delete' ? 'selected bolder' : ""}`}
                                onClick={this.setDelete}>
                            delete
                        </button>
                        <button className={`edit ${this.state.form === 'edit' ? 'selected bolder' : ""}`}
                                onClick={this.setEdit}>
                            edit
                        </button>
                        {canMove ? (
                            <button className={`move ${this.state.form === 'move' ? 'selected bolder' : ""}`}
                                    onClick={this.setMove}>
                                move
                            </button>
                        ) : ""}
                    </div>
                    <div className={`form position-relative flex-grow-1 text-center ${this.state.form}`}>
                        {this.renderForm()}
                    </div>
                </div>
            </Dialog>
        );
    }

    renderForm() {
        switch (this.state.form) {
            case 'delete':
                return this.renderDelete();
            case 'edit':
                return this.renderEdit();
            case 'move':
                if (this.props.values.length === 1)
                    return this.renderMove();
                break;
            default:
                break;
        }
    }

    renderDelete() {
        return (
            <div className="flex-grow-1">
                {markdownToReact(formatString(
                    PYTHON_LANG.form_content_delete_prop_val,
                    {name: this.props.name, value: this.valuesToString()}
                ))}
            </div>
        );
    }

    renderEdit() {
        const name = this.props.name;
        const propVal = this.state.value;
        const def = this.props.properties[name];

        let input;
        if (def.enumeration) {
            input = (
                <select value={propVal} onChange={this.onEdit}>
                    {def.enumeration.map((value, valueIndex) =>
                        <option key={valueIndex} value={value}>{value}</option>)}
                </select>
            );
        } else if (def.type === "bool") {
            input = (
                <select value={propVal} onChange={this.onEdit}>
                    <option value="false">false</option>
                    <option value="true">true</option>
                </select>
            );
        } else {
            input = <input type={def.type === "int" ? "number" : "text"}
                           onChange={this.onEdit}
                           value={propVal}
                           onKeyDown={this.onEditKeyDown}/>;
        }
        return (
            <div className="flex-grow-1">
                <h3>{formatString(PYTHON_LANG.form_content_edit_prop_val, {name: this.props.name, value: this.valuesToString()})}</h3>
                <div>{input}</div>
            </div>
        );
    }

    renderMove() {
        const def = this.props.properties[this.props.name];
        return (
            <div className="flex-grow-1">
                <h3>
                    {formatString(
                        PYTHON_LANG.form_content_move_prop_val,
                        {name: this.props.name, value: this.valuesToString(), type: def.type}
                    )}
                </h3>
                <div>
                    <select value={this.state.move} onChange={this.onMove}>
                        {this.state.otherDefinitions.map((other, index) =>
                            <option key={index} value={other.name}>{other.name}</option>)}
                    </select>
                </div>
            </div>
        );
    }

    getCompatibleDefinitions() {
        const def = this.props.properties[this.props.name];
        const otherDefinitions = [];
        for (let other of Object.values(this.props.properties)) {
            if (def.name !== other.name && def.type === other.type)
                otherDefinitions.push(other);
        }
        return otherDefinitions;
    }

    setDelete() {
        this.setState({form: 'delete'});
    }

    setEdit() {
        this.setState({form: 'edit', value: this.props.value});
    }

    setMove() {
        this.setState({form: 'move', move: this.state.otherDefinitions[0].name});
    }

    onEdit(event) {
        const def = this.props.properties[this.props.name];
        try {
            this.setState({value: parsePropValString(def.type, def.enumeration, event.target.value)});
        } catch (exception) {
            window.alert(exception.toString());
        }
    }

    onEditKeyDown(event) {
        if (event.key === "Enter") {
            Fancybox.close();
            this.onClose();
        }
    }

    onMove(event) {
        this.setState({move: event.target.value});
    }

    onClose() {
        this.props.onClose(Object.assign({}, this.state));
    }

    valuesToString() {
        if (this.props.values.length === 1)
            return this.props.values[0].toString();
        return formatString(
            PYTHON_LANG.form_summary_values,
            {
                count: this.props.values.length,
                first: this.props.values[0],
                last: this.props.values[this.props.values.length - 1]
            }
        );
    }
}

FormPropertyEditSelectedValues.propTypes = {
    properties: PropTypes.object.isRequired,
    name: PropTypes.string.isRequired,
    values: PropTypes.array.isRequired,
    // onClose(object)
    onClose: PropTypes.func.isRequired
};
