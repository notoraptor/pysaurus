import {Dialog} from "./Dialog.js";
import {Cell} from "./Cell.js";

export class FormSetClassification extends React.Component {
    constructor(props) {
        // properties: PropertyDefinition[]
        // onClose(name)
        super(props);
        this.state = {field: this.props.properties[0].name};
        this.onChangeGroupField = this.onChangeGroupField.bind(this);
        this.onClose = this.onClose.bind(this);
    }
    render() {
        return (
            <Dialog yes={"classify"} no={"cancel"} onClose={this.onClose}>
                <Cell center={true} full={true} className="text-center">
                    <select value={this.state.field}
                            onChange={this.onChangeGroupField}>
                        {this.props.properties.map((def, i) => (
                            <option key={i} value={def.name}>Property: {def.name}</option>
                        ))}
                    </select>
                </Cell>
            </Dialog>
        );
    }
    onChangeGroupField(event) {
        this.setState({field: event.target.value});
    }
    onClose(yes) {
        this.props.onClose(yes ? this.state.field: null);
    }
}