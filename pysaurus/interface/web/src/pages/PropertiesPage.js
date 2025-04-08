import { BaseComponent } from "../BaseComponent.js";
import { Cell } from "../components/Cell.js";
import { ComponentPropController, SetInput } from "../components/SetInput.js";
import { Dialog } from "../dialogs/Dialog.js";
import { GenericFormRename } from "../forms/GenericFormRename.js";
import { tr } from "../language.js";
import { Fancybox } from "../utils/FancyboxManager.js";
import { backend_error, python_multiple_call } from "../utils/backend.js";
import { UTILITIES } from "../utils/functions.js";

const DEFAULT_VALUES = {
	bool: false,
	int: 0,
	float: 0.0,
	str: "",
};

function getDefaultValue(propType, isEnum) {
	return isEnum ? [] : DEFAULT_VALUES[propType].toString();
}

export class PropertiesPage extends BaseComponent {
	// app: App
	// parameters {definitions}

	getInitialState() {
		const definitions = this.props.parameters.definitions;
		const defaultType = "str";
		return {
			definitions: definitions,
			name: "",
			type: defaultType,
			enumeration: true,
			defaultPropVal: getDefaultValue(defaultType, true),
			multiple: false,
		};
	}

	render() {
		return (
			<div id="properties">
				<h2 className="horizontal ml-1 mr-1">
					<div className="back position-relative">
						<button className="block h-100 px-4" onClick={this.back}>
							<strong>&#11164;</strong>
						</button>
					</div>
					<div className="text-center flex-grow-1">{tr("Properties Management")}</div>
				</h2>
				<hr />
				<div className="content horizontal">
					<div className="list text-center">
						<h3 className="text-center">{tr("Current properties")}</h3>
						{this.renderPropTypes()}
					</div>
					<div className="new">
						<h3 className="text-center">{tr("Add a new property")}</h3>
						<table className="first-td-text-right w-100">
							<tbody>
								<tr>
									<td>
										<label htmlFor="prop-name">Name:</label>
									</td>
									<td>
										<input
											type="text"
											id="prop-name"
											className="block"
											value={this.state.name}
											onChange={this.onChangeName}
										/>
									</td>
								</tr>
								<tr>
									<td>
										<label htmlFor="prop-type">Type:</label>
									</td>
									<td>
										<select
											id="prop-type"
											className="block"
											value={this.state.type}
											onChange={this.onChangeType}>
											<option value="bool">{tr("boolean")}</option>
											<option value="int">{tr("integer")}</option>
											<option value="float">{tr("floating number")}</option>
											<option value="str">{tr("text")}</option>
										</select>
									</td>
								</tr>
								<tr>
									<td>
										<input
											type="checkbox"
											id="prop-multiple"
											checked={this.state.multiple}
											onChange={this.onChangeMultiple}
										/>
									</td>
									<td>
										<label htmlFor="prop-multiple">{tr("accept many values")}</label>
									</td>
								</tr>
								<tr>
									<td>
										<input
											type="checkbox"
											id="prop-enumeration"
											checked={this.state.enumeration}
											onChange={this.onChangeEnumeration}
										/>
									</td>
									<td>
										<label htmlFor="prop-enumeration">{tr("Is enumeration")}</label>
									</td>
								</tr>
								{!this.state.multiple || this.state.enumeration ? (
									<tr>
										<td>
											<label htmlFor={"prop-default-" + this.state.type}>
												{this.state.enumeration
													? this.state.multiple
														? tr("Enumeration values (first is default)")
														: tr("Enumeration values")
													: tr("Default value")}
											</label>
										</td>
										<td>{this.renderDefaultInput()}</td>
									</tr>
								) : (
									""
								)}
								<tr className="buttons">
									<td>
										<button className="reset block" onClick={this.reset}>
											reset
										</button>
									</td>
									<td>
										<button className="submit block" onClick={this.submit}>
											<strong>add</strong>
										</button>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>
		);
	}

	renderPropTypes() {
		return (
			<table className="w-100">
				<thead className="bold">
					<tr>
						<th>Name</th>
						<th>Type</th>
						<th>Default</th>
						<th>Options</th>
					</tr>
				</thead>
				<tbody>
					{this.state.definitions.map((def, index) => (
						<tr key={index}>
							<td className="name">
								<strong>{def.name}</strong>
							</td>
							<td className="type">
								{def.multiple ? <span>{tr("one or many")}&nbsp;</span> : ""}
								<span>
									<code>{def.type}</code> {def.multiple ? tr("values") : tr("value")}
								</span>
								{def.enumeration ? (
									<span>
										&nbsp;{tr("in")} {"{"}
										{def.enumeration.join(", ")}
										{"}"}
									</span>
								) : (
									""
								)}
							</td>
							<td className="default">
								{(function () {
									let values = def.defaultValues;
									if (def.type === "str") values = values.map((el) => `"${el}"`);
									else values = values.map((el) => el.toString());
									let output = values.join(", ");
									if (def.multiple) {
										output = `{${output}}`;
									}
									return output;
								})()}
							</td>
							<td className="options">
								<div>
									<button className="delete red-flag" onClick={() => this.deleteProperty(def.name)}>
										delete
									</button>
								</div>
								<div>
									<button className="rename" onClick={() => this.renameProperty(def.name)}>
										rename
									</button>
								</div>
								{def.multiple ? (
									<div>
										<button
											className="convert-to-unique"
											onClick={() => this.convertPropertyToUnique(def.name)}>
											convert to unique
										</button>
									</div>
								) : (
									<div>
										<button
											className="convert-to-multiple"
											onClick={() => this.convertPropertyToMultiple(def.name)}>
											convert to multiple
										</button>
									</div>
								)}
							</td>
						</tr>
					))}
				</tbody>
			</table>
		);
	}

	renderDefaultInput() {
		if (this.state.enumeration) {
			const controller = new ComponentPropController(this, "defaultPropVal", this.state.type, null);
			return (
				<SetInput className="block" identifier={"prop-default-" + this.state.type} controller={controller} />
			);
		}
		if (this.state.type === "bool") {
			return (
				<select
					className="prop-default block"
					id="prop-default-bool"
					value={this.state.defaultPropVal}
					onChange={this.onChangeDefault}>
					<option value="false">false</option>
					<option value="true">true</option>
				</select>
			);
		}
		return (
			<input
				type={this.state.type === "int" ? "number" : "text"}
				className="prop-default block"
				id={"prop-default-" + this.state.type}
				onChange={this.onChangeDefault}
				value={this.state.defaultPropVal}
			/>
		);
	}

	back() {
		this.props.app.loadVideosPage();
	}

	onChangeName(event) {
		const name = event.target.value;
		if (this.state.name !== name) this.setState({ name });
	}

	onChangeType(event) {
		const value = event.target.value;
		if (this.state.type !== value)
			this.setState({
				type: value,
				enumeration: false,
				defaultPropVal: getDefaultValue(value),
				multiple: false,
			});
	}

	onChangeDefault(event) {
		const defaultPropVal = event.target.value;
		if (this.state.defaultPropVal !== defaultPropVal) this.setState({ defaultPropVal });
	}

	onChangeMultiple(event) {
		this.setState({ multiple: event.target.checked });
	}

	onChangeEnumeration(event) {
		const enumeration = event.target.checked;
		const defaultPropVal = getDefaultValue(this.state.type, enumeration);
		this.setState({ enumeration, defaultPropVal });
	}

	reset() {
		this.setState(this.getDefaultInputState());
	}

	submit() {
		try {
			let definition = this.state.defaultPropVal;
			if (!this.state.enumeration) definition = UTILITIES.parsePropValString(this.state.type, null, definition);
			python_multiple_call(
				["create_prop_type", this.state.name, this.state.type, definition, this.state.multiple],
				["describe_prop_types"]
			)
				.then((definitions) => {
					const state = this.getDefaultInputState();
					state.definitions = definitions;
					this.setState(state);
				})
				.catch(backend_error);
		} catch (exception) {
			window.alert(exception.toString());
		}
	}

	deleteProperty(name) {
		Fancybox.load(
			<Dialog
				title={tr('Delete property "{name}"?', { name })}
				yes={tr("DELETE")}
				action={() => {
					python_multiple_call(["remove_prop_type", name], ["describe_prop_types"])
						.catch(backend_error)
						.then((definitions) => {
							const state = this.getDefaultInputState();
							state.definitions = definitions;
							this.setState(state);
						});
				}}>
				<Cell className="text-center" center={true} full={true}>
					<h3>
						{tr('Are you sure you want to delete property "{name}"?', {
							name,
						})}
					</h3>
				</Cell>
			</Dialog>
		);
	}

	convertPropertyToUnique(name) {
		Fancybox.load(
			<Dialog
				title={tr('Convert to unique property "{name}"?', {
					name,
				})}
				yes={tr("convert to unique")}
				action={() => {
					python_multiple_call(["convert_prop_multiplicity", name, false], ["describe_prop_types"])
						.then((definitions) => {
							const state = this.getDefaultInputState();
							state.definitions = definitions;
							this.setState(state);
						})
						.catch(backend_error);
				}}>
				<Cell className="text-center" center={true} full={true}>
					<h3>
						{tr('Are you sure you want to convert to unique property "{name}"?', {
							name,
						})}
					</h3>
				</Cell>
			</Dialog>
		);
	}

	convertPropertyToMultiple(name) {
		Fancybox.load(
			<Dialog
				title={tr('Convert to multiple property "{name}"?', {
					name,
				})}
				yes={tr("convert to multiple")}
				action={() => {
					python_multiple_call(["convert_prop_multiplicity", name, true], ["describe_prop_types"])
						.then((definitions) => {
							const state = this.getDefaultInputState();
							state.definitions = definitions;
							this.setState(state);
						})
						.catch(backend_error);
				}}>
				<Cell className="text-center" center={true} full={true}>
					<h3>
						{tr('Are you sure you want to convert to multiple property "{name}"?', {
							name,
						})}
					</h3>
				</Cell>
			</Dialog>
		);
	}

	renameProperty(name) {
		Fancybox.load(
			<GenericFormRename
				title={tr('Rename property "{name}"?', { name })}
				header={tr("Rename property")}
				description={name}
				data={name}
				onClose={(newName) => {
					python_multiple_call(["rename_prop_type", name, newName], ["describe_prop_types"])
						.then((definitions) => {
							const state = this.getDefaultInputState();
							state.definitions = definitions;
							this.setState(state);
						})
						.catch(backend_error);
				}}
			/>
		);
	}

	getDefaultInputState() {
		const defaultType = "str";
		return {
			name: "",
			type: defaultType,
			enumeration: false,
			defaultPropVal: getDefaultValue(defaultType),
			multiple: false,
		};
	}
}
