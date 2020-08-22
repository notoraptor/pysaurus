import {SORTED_FIELDS_AND_TITLES} from "./constants.js";


const REVERSE_VALUES = {"true": true, "false": false};

export class FormGroup extends React.Component {
    constructor(props) {
        // field
        // reverse
        // onClose
        super(props);
        this.state = {
            field: this.props.field || '',
            reverse: this.props.reverse || '',
        };
        this.onChangeGroupField = this.onChangeGroupField.bind(this);
        this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
    }
    render() {
        return (
            <div className="form-group">
                <p>
                    <select id="group-field"
                            name="groupField"
                            value={this.state.field}
                            onChange={this.onChangeGroupField}>
                        {SORTED_FIELDS_AND_TITLES.map((entry, fieldIndex) => (
                            <option key={fieldIndex} value={entry[0]}>{entry[1]}</option>
                        ))}
                    </select>
                </p>
                <p>
                    <input type="radio"
                           id="group-reverse-off"
                           name="groupReverse"
                           value={false}
                           checked={this.state.reverse === false}
                           onChange={this.onChangeGroupReverse}/>
                    <label htmlFor="group-reverse-off"> ascending</label>
                </p>
                <p>
                    <input type="radio"
                           id="group-reverse-on"
                           name="groupReverse"
                           value={true}
                           checked={this.state.reverse === true}
                           onChange={this.onChangeGroupReverse}/>
                    <label htmlFor="group-reverse-on"> descending</label>
                </p>
            </div>
        );
    }
    onChangeGroupField(event) {
        this.setState({field: event.target.value, reverse: ''});
    }
    onChangeGroupReverse(event) {
        const field = this.state.field || document.querySelector('#group-field').value;
        const reverse = REVERSE_VALUES[event.target.value];
        this.setState({reverse}, () => this.props.onClose({field, reverse}));
    }
}