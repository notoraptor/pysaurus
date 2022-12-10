import { FIELD_MAP } from "../utils/constants.js";
import { FancyBox } from "../dialogs/FancyBox.js";
import { LangContext, tr } from "../language.js";
import { Fancybox } from "../utils/FancyboxManager.js";

export class FormVideosSort extends React.Component {
	constructor(props) {
		// sorting
		// onClose(sorting)
		super(props);
		const sorting = this.props.sorting.length ? this.props.sorting : ["-date"];
		this.state = { sorting: sorting };
		this.setField = this.setField.bind(this);
		this.setReverse = this.setReverse.bind(this);
		this.addCriterion = this.addCriterion.bind(this);
		this.removeCriterion = this.removeCriterion.bind(this);
		this.submit = this.submit.bind(this);
	}

	render() {
		return (
			<FancyBox title={tr("Sort videos")}>
				<div id="form-videos-sort" className="form absolute-plain vertical text-center p-2">
					<div className="help mb-4">
						{tr(
							`
Click on "+" to add a new sorting criterion.

Click on "-" to remove a sorting criterion.

Click on "sort" to validate, or close dialog to cancel.
`,
							null,
							"markdown"
						)}
					</div>
					<div id="sorting" className="flex-grow-1 overflow-auto">
						{this.renderSorting()}
					</div>
					<p className="buttons flex-shrink-0 horizontal">
						<button className="add flex-grow-1 mr-1" onClick={this.addCriterion}>
							+
						</button>
						<button className="sort flex-grow-1 ml-2" onClick={this.submit}>
							<strong>sort</strong>
						</button>
					</p>
				</div>
			</FancyBox>
		);
	}

	renderSorting() {
		return this.state.sorting.map((def, index) => {
			const direction = def.charAt(0);
			const field = def.substr(1);
			const reverse = direction === "-";
			const reverseID = `reverse-${index}`;
			return (
				<p key={index} className="sorting">
					<button className="button-remove-sort" onClick={() => this.removeCriterion(index)}>
						-
					</button>
					<select value={field} onChange={(event) => this.setField(index, event.target.value)}>
						{FIELD_MAP.sortable.map((entry, fieldIndex) => (
							<option key={fieldIndex} value={entry.name}>
								{entry.title}
							</option>
						))}
					</select>
					<input
						type="checkbox"
						id={reverseID}
						checked={reverse}
						onChange={(event) => this.setReverse(index, event.target.checked)}
					/>
					<label htmlFor={reverseID}>reverse</label>
				</p>
			);
		});
	}

	setField(index, value) {
		const sorting = this.state.sorting.slice();
		sorting[index] = `+${value}`;
		this.setState({ sorting });
	}

	setReverse(index, checked) {
		const sorting = this.state.sorting.slice();
		sorting[index] = (checked ? "-" : "+") + sorting[index].substr(1);
		this.setState({ sorting });
	}

	addCriterion() {
		const sorting = this.state.sorting.slice();
		sorting.push("+title");
		this.setState({ sorting });
	}

	removeCriterion(index) {
		const sorting = this.state.sorting.slice();
		sorting.splice(index, 1);
		this.setState({ sorting });
	}

	submit() {
		const sorting = [];
		for (let def of this.state.sorting) {
			if (sorting.indexOf(def) < 0) sorting.push(def);
		}
		Fancybox.close();
		if (sorting.length) this.props.onClose(sorting);
	}
}

FormVideosSort.contextType = LangContext;
