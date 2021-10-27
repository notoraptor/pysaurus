class SetController {
    constructor() {
    }

    size() {
    }

    get(index) {
    }

    has(value) {
    }

    add(value) {
    }

    remove(value) {
    }
}

export class ComponentController extends SetController {
    constructor(app, field, parser = null) {
        super();
        this.app = app;
        this.field = field;
        this.parser = parser;
    }

    size() {
        return this.app.state[this.field].length;
    }

    get(index) {
        return this.app.state[this.field][index];
    }

    has(value) {
        if (this.parser)
            value = this.parser(value);
        return this.app.state[this.field].indexOf(value) >= 0;
    }

    add(value) {
        const arr = this.app.state[this.field].slice();
        if (this.parser)
            value = this.parser(value);
        arr.push(value);
        this.app.setState({[this.field]: arr});
    }

    remove(toRemove) {
        if (this.parser)
            toRemove = this.parser(toRemove);
        const arr = [];
        for (let value of this.app.state[this.field]) {
            if (value !== toRemove)
                arr.push(value);
        }
        this.app.setState({[this.field]: arr});
    }
}

export class SetInput extends React.Component {
    constructor(props) {
        super(props);
        this.state = {add: this.props.values ? this.props.values[0] : ""};
        this.onChangeAdd = this.onChangeAdd.bind(this);
        this.onInputAdd = this.onInputAdd.bind(this);
        this.onAdd = this.onAdd.bind(this);
        this.add = this.add.bind(this);
        this.remove = this.remove.bind(this);
    }

    render() {
        return (
            <div className={`set-input ${this.props.className || ""}`}>
                <table className="first-td-text-right">
                    <tbody>
                    {this.renderList()}
                    <tr className="form">
                        <td>
                            {this.props.values ? (
                                <select value={this.state.add} onChange={this.onChangeAdd}>
                                    {this.props.values.map((value, index) => (
                                        <option key={index} value={value}>{value}</option>
                                    ))}
                                </select>
                            ) : (
                                <input type="text"
                                       value={this.state.add}
                                       onChange={this.onChangeAdd}
                                       onKeyDown={this.onInputAdd}
                                       size="10"
                                       {...(this.props.identifier ? {id: this.props.identifier} : {})}/>
                            )}
                        </td>
                        <td>
                            <button className="add block" onClick={this.onAdd}>+</button>
                        </td>
                    </tr>
                    </tbody>
                </table>
            </div>
        );
    }

    renderList() {
        const output = [];
        const controller = this.props.controller;
        const size = controller.size();
        for (let i = 0; i < size; ++i) {
            const value = controller.get(i);
            output.push(
                <tr className="item" key={i}>
                    <td>{value.toString()}</td>
                    <td>
                        <button className="remove block" onClick={() => this.remove(value)}>-</button>
                    </td>
                </tr>
            );
        }
        return output;
    }

    onChangeAdd(event) {
        this.setState({add: event.target.value});
    }

    onInputAdd(event) {
        if (event.key === "Enter") {
            this.add(this.state.add);
        }
    }

    onAdd() {
        this.add(this.state.add);
    }

    add(value) {
        if (!value.length)
            return;
        const controller = this.props.controller;
        try {
            if (controller.has(value))
                window.alert(PYTHON_LANG.alert_value_already_in_list.format({value}));
            else
                this.setState({add: ""}, () => controller.add(value));
        } catch (exception) {
            window.alert(exception.toString());
        }
    }

    remove(value) {
        const controller = this.props.controller;
        try {
            if (controller.has(value))
                controller.remove(value);
        } catch (e) {
            window.alert(e.toString());
        }
    }
}

SetInput.propTypes = {
    controller: PropTypes.instanceOf(SetController),
    identifier: PropTypes.string,
    values: PropTypes.array,
    className: PropTypes.string
}
