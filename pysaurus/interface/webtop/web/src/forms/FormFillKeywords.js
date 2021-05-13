import {Dialog} from "../dialogs/Dialog.js";
import {Cell} from "../components/Cell.js";

export class FormFillKeywords extends React.Component {
    constructor(props) {
        // properties: PropertyDefinition[]
        // onClose(name)
        super(props);
        this.state = {field: this.props.properties[0].name, onlyEmpty: false};
        this.onChangeGroupField = this.onChangeGroupField.bind(this);
        this.onChangeEmpty = this.onChangeEmpty.bind(this);
        this.onClose = this.onClose.bind(this);
    }
    render() {
        return (
            <Dialog yes={"fill"} no={"cancel"} onClose={this.onClose}>
                <Cell center={true} full={true} className="text-center">
                    <p>
                    <select value={this.state.field}
                            onChange={this.onChangeGroupField}>
                        {this.props.properties.map((def, i) => (
                            <option key={i} value={def.name}>Property: {def.name}</option>
                        ))}
                    </select>
                    </p>
                    <p>
                        <input id="only-empty" type="checkbox" checked={this.state.onlyEmpty} onChange={this.onChangeEmpty}/>
                        {' '}
                        <label htmlFor="only-empty">only videos without values for property "{this.state.field}"</label>
                    </p>
                </Cell>
            </Dialog>
        );
    }
    onChangeGroupField(event) {
        this.setState({field: event.target.value});
    }
    onChangeEmpty(event) {
        this.setState({onlyEmpty: event.target.checked});
    }
    onClose(yes) {
        this.props.onClose(yes ? this.state: null);
    }
}