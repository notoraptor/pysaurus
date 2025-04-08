import { Cell } from "../components/Cell.js";
import { Dialog } from "../dialogs/Dialog.js";
import { tr } from "../language.js";
import { BaseComponent } from "../BaseComponent.js";

export class FormVideosKeywordsToProperty extends BaseComponent {
	// prop_types: PropertyDefinition[]
	// onClose(name)

	getInitialState() {
		return { field: this.props.prop_types[0].name, onlyEmpty: false };
	}

	render() {
		return (
			<Dialog title="Fill property" yes={"fill"} action={this.onClose}>
				<Cell center={true} full={true} className="text-center">
					<p>
						<select value={this.state.field} onChange={this.onChangeGroupField}>
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
