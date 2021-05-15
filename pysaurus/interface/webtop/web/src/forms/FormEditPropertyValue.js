import {Dialog} from "../dialogs/Dialog.js";

export class FormEditPropertyValue extends React.Component {
    constructor(props) {
        // properties: {name => def}
        // name: str
        // values: []
        // onClose(operation)
        super(props);
        this.state = {
            form: 'edit',
            value: this.props.values[0].toString(),
            move: '',
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
        return (
            <Dialog yes={this.state.form} no="cancel" onClose={this.onClose}>
                <div className="edit-property-value">
                    <div className="bar text-center">
                        <button className={`delete ${this.state.form === 'delete' ? 'selected' : ''}`}
                                onClick={this.setDelete}>
                            delete
                        </button>
                        <button className={`edit ${this.state.form === 'edit' ? 'selected' : ''}`}
                                onClick={this.setEdit}>
                            edit
                        </button>
                        {canMove ? (
                            <button className={`move ${this.state.form === 'move' ? 'selected' : ''}`}
                                    onClick={this.setMove}>
                                move
                            </button>
                        ) : ''}
                    </div>
                    <div className={`form ${this.state.form}`}>
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
            <div>
                <h3>Are you sure you want to delete property value</h3>
                <h3>"{this.props.name}" / {this.valuesToString()} ?</h3>
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
            <div>
                <h3>Edit property "{this.props.name}" / {this.valuesToString()}</h3>
                <div>{input}</div>
            </div>
        );
    }

    renderMove() {
        const def = this.props.properties[this.props.name];
        return (
            <div>
                <h3>Move property "{this.props.name}" / {this.valuesToString()} to another property of type
                    "{def.type}".</h3>
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
            this.onClose(true);
        }
    }

    onMove(event) {
        this.setState({move: event.target.value});
    }

    onClose(yes) {
        this.props.onClose(yes ? Object.assign({}, this.state) : null);
    }

    valuesToString() {
        if (this.props.values.length === 1)
            return this.props.values[0].toString();
        return `${this.props.values.length} values (${this.props.values[0].toString()} ... ${this.props.values[this.props.values.length - 1].toString()})`;
    }
}
