import { BaseComponent } from "../BaseComponent.js";
import { ComponentPropController, SetInput } from "../components/SetInput.js";
import { Dialog } from "../dialogs/Dialog.js";
import { tr } from "../language.js";
import { UTILITIES } from "../utils/functions.js";

export class FormVideoEditProperties extends BaseComponent {
	// data
	// definitions
	// onClose

	getInitialState() {
		let state = {};
		const properties = this.props.data.properties;
		for (let def of this.props.definitions) {
			const name = def.name;
			state[name] = properties.hasOwnProperty(name) ? properties[name] : def.defaultValues;
		}
		return state;
	}

	render() {
		const data = this.props.data;
		const hasThumbnail = data.with_thumbnails;
		return (
			<Dialog title={tr("Edit video properties")} yes={tr("save")} action={this.onClose}>
				<div className="form-video-edit-properties horizontal">
					<div className="info">
						<div className="image">
							{hasThumbnail ? (
								<img alt={data.title} src={data.thumbnail_path} />
							) : (
								<div className="no-thumbnail">{tr("no thumbnail")}</div>
							)}
						</div>
						<div className="filename p-1 mb-1">
							<code>{data.filename}</code>
						</div>
						{data.title === data.file_title ? (
							""
						) : (
							<div className="title mb-1">
								<em>{data.title}</em>
							</div>
						)}
					</div>
					<div className="properties flex-grow-1">
						<table className="first-td-text-right w-100">
							<tbody>
								{this.props.definitions.map((def, index) => {
									const name = def.name;
									let input;
									if (def.multiple) {
										let possibleValues = null;
										if (def.enumeration) possibleValues = def.enumeration;
										else if (def.type === "bool") possibleValues = [false, true];
										const controller = new ComponentPropController(
											this,
											name,
											def.type,
											possibleValues,
										);
										input = <SetInput controller={controller} values={possibleValues} />;
									} else if (def.enumeration) {
										input = (
											<select
												value={this.state[name][0]}
												onChange={(event) => this.onChange(event, def)}>
												{def.enumeration.map((value, valueIndex) => (
													<option key={valueIndex} value={value}>
														{value}
													</option>
												))}
											</select>
										);
									} else if (def.type === "bool") {
										input = (
											<select
												value={this.state[name][0]}
												onChange={(event) => this.onChange(event, def)}>
												<option value="false">false</option>
												<option value="true">true</option>
											</select>
										);
									} else {
										input = (
											<input
												type={def.type === "int" ? "number" : "text"}
												onChange={(event) => this.onChange(event, def)}
												value={this.state[name][0]}
											/>
										);
									}
									return (
										<tr key={index}>
											<td className="label">
												<strong>{name}</strong>
											</td>
											<td className="input">{input}</td>
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>
				</div>
			</Dialog>
		);
	}

	onClose() {
		this.props.onClose(this.state);
	}

	onChange(event, def) {
		try {
			this.setState({
				[def.name]: [UTILITIES.parsePropValString(def.type, def.enumeration, event.target.value)],
			});
		} catch (exception) {
			window.alert(exception.toString());
		}
	}
}
