import {FIELD_MAP} from "../utils/constants.js";
import {FancyBox} from "../dialogs/FancyBox.js";

export class FormVideosSort extends React.Component {
    constructor(props) {
        // sorting
        // onClose(sorting)
        super(props);
        const sorting = this.props.sorting.length ? this.props.sorting : ['-date'];
        this.state = {sorting: sorting};
        this.setField = this.setField.bind(this);
        this.setReverse = this.setReverse.bind(this);
        this.addCriterion = this.addCriterion.bind(this);
        this.removeCriterion = this.removeCriterion.bind(this);
        this.submit = this.submit.bind(this);
    }

    render() {
        return (
            <FancyBox title="Sort videos">
                <div className="form vertical" id="form-sort">
                    <div className="help">
                        <div>Click on "+" to add a new sorting criterion.</div>
                        <div>Click on "-" to remove a sorting criterion.</div>
                        <div>Click on "sort" to validate, or close dialog to cancel.</div>
                    </div>
                    <div id="sorting">{this.renderSorting()}</div>
                    <p className="buttons horizontal">
                        <button className="add" onClick={this.addCriterion}>+</button>
                        <button className="sort" onClick={this.submit}>sort</button>
                    </p>
                </div>
            </FancyBox>
        );
    }

    renderSorting() {
        return this.state.sorting.map((def, index) => {
            const direction = def.charAt(0);
            const field = def.substr(1);
            const reverse = (direction === "-");
            const reverseID = `reverse-${index}`;
            return (
                <p key={index} className="sorting">
                    <button className="button-remove-sort" onClick={() => this.removeCriterion(index)}>-</button>
                    <select value={field} onChange={(event) => this.setField(index, event.target.value)}>
                        {FIELD_MAP.list.map(
                            (entry, fieldIndex) => (
                                <option key={fieldIndex} value={entry.name}>{entry.title}</option>
                            ))}
                    </select>
                    <input type="checkbox"
                           id={reverseID}
                           checked={reverse}
                           onChange={event => this.setReverse(index, event.target.checked)}/>
                    <label htmlFor={reverseID}>reverse</label>
                </p>
            );
        })
    };

    setField(index, value) {
        const sorting = this.state.sorting.slice();
        sorting[index] = `+${value}`;
        this.setState({sorting});
    }

    setReverse(index, checked) {
        const sorting = this.state.sorting.slice();
        sorting[index] = (checked ? '-' : '+') + sorting[index].substr(1);
        this.setState({sorting});
    }

    addCriterion() {
        const sorting = this.state.sorting.slice();
        sorting.push('+title');
        this.setState({sorting});
    }

    removeCriterion(index) {
        const sorting = this.state.sorting.slice();
        sorting.splice(index, 1);
        this.setState({sorting});
    }

    submit() {
        const sorting = [];
        for (let def of this.state.sorting) {
            if (sorting.indexOf(def) < 0)
                sorting.push(def);
        }
        Fancybox.close();
        if (sorting.length)
            this.props.onClose(sorting);
    }
}
