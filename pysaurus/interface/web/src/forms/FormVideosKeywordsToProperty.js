import { Dialog } from "../dialogs/Dialog.js";
import { Cell } from "../components/Cell.js";
import { LangContext, tr } from "../language.js";

export class FormVideosKeywordsToProperty extends React.Component {
	constructor(props) {
		// prop_types: PropertyDefinition[]
		// onClose(name)
		super(props);
		this.state = { field: this.props.prop_types[0].name, onlyEmpty: false };
		this.onChangeGroupField = this.onChangeGroupField.bind(this);
		this.onChangeEmpty = this.onChangeEmpty.bind(this);
		this.onClose = this.onClose.bind(this);
	}

	render() {
		return (
			<Dialog title="Fill property" yes={"fill"} action={this.onClose}>
				<Cell center={true} full={true} className="text-center">
					<p>
						<select
							value={this.state.field}
							onChange={this.onChangeGroupField}>
							{this.props.prop_types.map((def, i) => (
								<option key={i} value={def.name}>
									{tr("Property")}: {def.name}
								</option>
							))}
						</select>
					</p>
					<p>
						<input
							id="only-empty"
							type="checkbox"
							checked={this.state.onlyEmpty}
							onChange={this.onChangeEmpty}
						/>{" "}
						<label htmlFor="only-empty">
							{tr('only videos without values for property "{name}"', {
								name: this.state.field,
							})}
						</label>
					</p>
				</Cell>
			</Dialog>
		);
	}

	onChangeGroupField(event) {
		this.setState({ field: event.target.value });
	}

	onChangeEmpty(event) {
		this.setState({ onlyEmpty: event.target.checked });
	}

	onClose() {
		this.props.onClose(this.state);
	}
}

FormVideosKeywordsToProperty.contextType = LangContext;
