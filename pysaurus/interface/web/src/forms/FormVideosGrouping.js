import { getFieldMap } from "../utils/constants.js";
import { Dialog } from "../dialogs/Dialog.js";
import { LangContext } from "../language.js";

export class FormVideosGrouping extends React.Component {
	constructor(props) {
		// groupDef: GroupDef
		// prop_types: [PropDef]
		// propertyMap: {name: PropDef}
		// onClose(groupDef)
		super(props);
		this.state = this.props.groupDef.field
			? {
					isProperty: this.props.groupDef.is_property,
					field: this.props.groupDef.field,
					sorting: this.props.groupDef.sorting,
					reverse: this.props.groupDef.reverse,
					allowSingletons: this.props.groupDef.allow_singletons,
			  }
			: {
					isProperty: false,
					field: undefined,
					sorting: "field",
					reverse: false,
					allowSingletons: undefined,
			  };
		this.onChangeAllowSingletons = this.onChangeAllowSingletons.bind(this);
		this.onChangeGroupField = this.onChangeGroupField.bind(this);
		this.onChangeSorting = this.onChangeSorting.bind(this);
		this.onChangeGroupReverse = this.onChangeGroupReverse.bind(this);
		this.onClose = this.onClose.bind(this);
		this.onChangeFieldType = this.onChangeFieldType.bind(this);
		this.getFields = this.getFields.bind(this);
		this.getStateField = this.getStateField.bind(this);
		this.getStateAllowSingletons = this.getStateAllowSingletons.bind(this);
	}

	render() {
		const field = this.getStateField();
		return (
			<Dialog title={"Group videos:"} yes="group" action={this.onClose}>
				<table className="from-videos-grouping first-td-text-right w-100">
					<tbody>
						<tr>
							<td className="label">{this.context.text_field_type}</td>
							<td>
								<input
									id="field-type-property"
									type="radio"
									value="true"
									checked={this.state.isProperty}
									onChange={this.onChangeFieldType}
								/>{" "}
								<label htmlFor="field-type-property">property</label>{" "}
								<input
									id="field-type-attribute"
									type="radio"
									value="false"
									checked={!this.state.isProperty}
									onChange={this.onChangeFieldType}
								/>{" "}
								<label htmlFor="field-type-attribute">attribute</label>
							</td>
						</tr>
						<tr>
							<td className="label">
								<label htmlFor="group-field">Field</label>
							</td>
							<td>
								<select
									className="block"
									id="group-field"
									value={field}
									onChange={this.onChangeGroupField}>
									{this.state.isProperty
										? this.props.prop_types.map((def, index) => (
												<option key={index} value={def.name}>
													{def.name}
												</option>
										  ))
										: this.getFields().allowed.map(
												(fieldOption, index) => (
													<option
														key={index}
														value={fieldOption.name}>
														{fieldOption.title}
													</option>
												)
										  )}
								</select>
							</td>
						</tr>
						{this.state.isProperty ||
						!this.getFields().fields[field].isOnlyMany() ? (
							<tr>
								<td className="label">
									<input
										type="checkbox"
										id="allow-singletons"
										checked={this.getStateAllowSingletons()}
										onChange={this.onChangeAllowSingletons}
									/>
								</td>
								<td>
									<label htmlFor="allow-singletons">
										{this.context.text_allow_singletons}
									</label>
								</td>
							</tr>
						) : (
							<tr>
								<td>&nbsp;</td>
								<td>
									<em>
										{this.context.text_singletons_auto_disabled}
									</em>
								</td>
							</tr>
						)}
						<tr>
							<td className="label">
								<label htmlFor="group-sorting">
									{this.context.text_sort_using}
								</label>
							</td>
							<td>
								<select
									className="block"
									id="group-sorting"
									value={this.state.sorting}
									onChange={this.onChangeSorting}>
									<option value="field">
										{this.context.text_field_value}
									</option>
									{this.fieldIsString() ? (
										<option value="length">
											{this.context.text_field_value_length}
										</option>
									) : (
										""
									)}
									<option value="count">
										{this.context.text_group_size}
									</option>
								</select>
							</td>
						</tr>
						<tr>
							<td className="label">
								<input
									type="checkbox"
									id="group-reverse"
									checked={this.state.reverse}
									onChange={this.onChangeGroupReverse}
								/>
							</td>
							<td>
								<label htmlFor="group-reverse">
									{this.context.text_sort_reverse}
								</label>
							</td>
						</tr>
					</tbody>
				</table>
			</Dialog>
		);
	}

	getStateField() {
		return this.state.field === undefined
			? this.getFields().allowed[0].name
			: this.state.field;
	}

	getStateAllowSingletons() {
		return this.state.allowSingletons === undefined
			? !this.getFields().allowed[0].isOnlyMany()
			: this.state.allowSingletons;
	}

	getFields() {
		return getFieldMap(this.context);
	}

	fieldIsString() {
		const field = this.getStateField();
		if (this.state.isProperty) return this.props.propertyMap[field].type === "str";
		return this.getFields().fields[field].isString();
	}

	onChangeFieldType(event) {
		const isProperty = event.target.value === "true";
		const field = isProperty
			? this.props.prop_types[0].name
			: this.getFields().allowed[0].name;
		const sorting = "field";
		const reverse = false;
		const allowSingletons = isProperty || !this.getFields().allowed[0].isOnlyMany();
		this.setState({ isProperty, field, sorting, reverse, allowSingletons });
	}

	onChangeGroupField(event) {
		const field = event.target.value;
		const sorting = "field";
		const reverse = false;
		const allowSingletons =
			this.state.isProperty || !this.getFields().fields[field].isOnlyMany();
		this.setState({ field, sorting, reverse, allowSingletons });
	}

	onChangeAllowSingletons(event) {
		this.setState({ allowSingletons: event.target.checked });
	}

	onChangeSorting(event) {
		this.setState({ sorting: event.target.value, reverse: false });
	}

	onChangeGroupReverse(event) {
		this.setState({ reverse: event.target.checked });
	}

	onClose() {
		this.props.onClose(
			Object.assign(
				{},
				{
					isProperty: this.state.isProperty,
					field: this.getStateField(),
					sorting: this.state.sorting,
					reverse: this.state.reverse,
					allowSingletons: this.getStateAllowSingletons(),
				}
			)
		);
	}
}
FormVideosGrouping.contextType = LangContext;
