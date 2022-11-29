import { Dialog } from "../dialogs/Dialog.js";
import { Characters } from "../utils/constants.js";
import { LangContext } from "../language.js";
import { utilities } from "../utils/functions.js";

export class FormSelectedVideosEditProperty extends React.Component {
	constructor(props) {
		// nbVideos
		// definition: property definition
		// values: [(value, count)]
		// onClose
		super(props);
		const current = [];
		for (let valueAndCount of this.props.values) {
			current.push(valueAndCount[0]);
		}
		this.state = {
			current: current,
			add: [],
			remove: [],
			value: this.getDefaultValue(),
		};
		this.onEdit = this.onEdit.bind(this);
		this.onEditKeyDown = this.onEditKeyDown.bind(this);
		this.onAddNewValue = this.onAddNewValue.bind(this);
		this.remove = this.remove.bind(this);
		this.add = this.add.bind(this);
		this.unRemove = this.unRemove.bind(this);
		this.unAdd = this.unAdd.bind(this);
		this.onClose = this.onClose.bind(this);
		this.unRemoveAll = this.unRemoveAll.bind(this);
		this.removeAll = this.removeAll.bind(this);
		this.addAll = this.addAll.bind(this);
		this.unAddAll = this.unAddAll.bind(this);
	}

	getMapping() {
		const mapping = new Map();
		for (let valueAndCount of this.props.values) {
			mapping.set(valueAndCount[0], valueAndCount[1]);
		}
		return mapping;
	}

	render() {
		const propName = this.props.definition.name;
		const nbVideos = this.props.nbVideos;
		return (
			<Dialog
				title={tr('Edit property "{name}" for {count} video(s)', {
					name: propName,
					count: nbVideos,
				})}
				yes="edit"
				action={this.onClose}>
				<div className="form-selected-videos-edit-property vertical flex-grow-1 text-center">
					<div className="bar titles flex-shrink-0 horizontal bold">
						<div>{tr("To remove")}</div>
						<div>{tr("Current")}</div>
						<div>{tr("To add")}</div>
					</div>
					<div className="bar panels horizontal flex-grow-1">
						<div className="remove">{this.renderRemove()}</div>
						<div className="current">{this.renderCurrent()}</div>
						<div className="add">{this.renderAdd()}</div>
					</div>
					<div className="bar new flex-shrink-0 all horizontal">
						{this.state.remove.length > 1 ? (
							<div className="horizontal">
								<div className="value">
									{tr("all {count} values", {
										count: this.state.remove.length,
									})}
								</div>
								<button onClick={this.unRemoveAll}>
									{Characters.SMART_ARROW_RIGHT}
								</button>
							</div>
						) : (
							<div />
						)}
						{this.state.current.length > 1 ? (
							<div className="horizontal">
								<button onClick={this.removeAll}>
									{Characters.SMART_ARROW_LEFT}
								</button>
								<div className="value">
									{tr("all {count} values", {
										count: this.state.current.length,
									})}
								</div>
								{this.props.definition.multiple ? (
									<button onClick={this.addAll}>
										{Characters.SMART_ARROW_RIGHT}
									</button>
								) : (
									""
								)}
							</div>
						) : (
							<div />
						)}
						{this.state.add.length > 1 ? (
							<div className="horizontal">
								<button onClick={this.unAddAll}>
									{Characters.SMART_ARROW_LEFT}
								</button>
								<div className="value">
									{tr("all {count} values", {
										count: this.state.add.length,
									})}
								</div>
							</div>
						) : (
							<div />
						)}
					</div>
					{this.renderFormAdd()}
				</div>
			</Dialog>
		);
	}

	renderRemove() {
		return this.state.remove.map((value, index) => (
			<div key={index} className="entry horizontal">
				<div className="value">{value}</div>
				<button onClick={() => this.unRemove(value)}>
					{Characters.SMART_ARROW_RIGHT}
				</button>
			</div>
		));
	}

	renderCurrent() {
		return this.state.current.map((value, index) => (
			<div key={index} className="entry horizontal">
				<button onClick={() => this.remove(value)}>
					{Characters.SMART_ARROW_LEFT}
				</button>
				<div className="value">
					{value}{" "}
					<em>
						<strong>({this.getMapping().get(value)})</strong>
					</em>
				</div>
				<button onClick={() => this.add(value)}>
					{Characters.SMART_ARROW_RIGHT}
				</button>
			</div>
		));
	}

	renderAdd() {
		return this.state.add.map((value, index) => (
			<div key={index} className="entry horizontal">
				<button onClick={() => this.unAdd(value)}>
					{this.getMapping().has(value) ? Characters.SMART_ARROW_LEFT : "-"}
				</button>
				<div className="value">{value}</div>
			</div>
		));
	}

	getDefaultValue() {
		const def = this.props.definition;
		if (def.enumeration) return def.enumeration[0];
		if (def.type === "bool") return "false";
		if (def.type === "int") return "0";
		return "";
	}

	renderFormAdd() {
		const def = this.props.definition;
		let input;
		if (def.enumeration) {
			input = (
				<select onChange={this.onEdit} value={this.state.value}>
					{def.enumeration.map((value, valueIndex) => (
						<option key={valueIndex} value={value}>
							{value}
						</option>
					))}
				</select>
			);
		} else if (def.type === "bool") {
			input = (
				<select onChange={this.onEdit} value={this.state.value}>
					<option value="false">false</option>
					<option value="true">true</option>
				</select>
			);
		} else {
			input = (
				<input
					type={def.type === "int" ? "number" : "text"}
					onChange={this.onEdit}
					value={this.state.value}
					onKeyDown={this.onEditKeyDown}
				/>
			);
		}
		return (
			<div className="bar new flex-shrink-0 horizontal">
				<div />
				<div />
				<div className="horizontal">
					<div>{input}</div>
					<button
						className="add-new-value flex-grow-1 ml-1"
						onClick={this.onAddNewValue}>
						add
					</button>
				</div>
			</div>
		);
	}

	onEdit(event) {
		const def = this.props.definition;
		try {
			this.setState({
				value: utilities(this.context).parsePropValString(
					def.type,
					def.enumeration,
					event.target.value
				),
			});
		} catch (exception) {
			window.alert(exception.toString());
		}
	}

	onEditKeyDown(event) {
		if (event.key === "Enter") {
			this.onAddNewValue();
		}
	}

	onAddNewValue() {
		if (this.state.value !== null) {
			if (this.props.definition.multiple) {
				const add = new Set(this.state.add);
				add.add(this.state.value);
				const output = Array.from(add);
				output.sort();
				this.setState({ add: output, value: this.getDefaultValue() });
			} else {
				const add = [this.state.value];
				const current = [];
				const remove = Array.from(this.getMapping().keys());
				remove.sort();
				this.setState({
					remove,
					current,
					add,
					value: this.getDefaultValue(),
				});
			}
		}
	}

	remove(value) {
		const current = new Set(this.state.current);
		const remove = new Set(this.state.remove);
		current.delete(value);
		remove.add(value);
		const newCurrent = Array.from(current);
		const newRemove = Array.from(remove);
		newCurrent.sort();
		newRemove.sort();
		this.setState({ current: newCurrent, remove: newRemove });
	}

	removeAll() {
		const remove = new Set(this.state.remove);
		this.state.current.forEach(remove.add, remove);
		const newCurrent = [];
		const newRemove = Array.from(remove);
		newRemove.sort();
		this.setState({ current: newCurrent, remove: newRemove });
	}

	add(value) {
		if (this.props.definition.multiple) {
			const current = new Set(this.state.current);
			const add = new Set(this.state.add);
			current.delete(value);
			add.add(value);
			const newCurrent = Array.from(current);
			const newAdd = Array.from(add);
			newCurrent.sort();
			newAdd.sort();
			this.setState({ current: newCurrent, add: newAdd });
		} else {
			const add = [value];
			const current = [];
			const setRemove = new Set(this.getMapping().keys());
			setRemove.delete(value);
			const remove = Array.from(setRemove);
			remove.sort();
			this.setState({ remove, current, add });
		}
	}

	addAll() {
		const add = new Set(this.state.add);
		this.state.current.forEach(add.add, add);
		const newCurrent = [];
		const newAdd = Array.from(add);
		newAdd.sort();
		this.setState({ current: newCurrent, add: newAdd });
	}

	unRemove(value) {
		const current = new Set(this.state.current);
		const remove = new Set(this.state.remove);
		remove.delete(value);
		current.add(value);
		const newCurrent = Array.from(current);
		const newRemove = Array.from(remove);
		newCurrent.sort();
		newRemove.sort();
		this.setState({ current: newCurrent, remove: newRemove });
	}

	unRemoveAll() {
		const current = new Set(this.state.current);
		this.state.remove.forEach(current.add, current);
		const newCurrent = Array.from(current);
		const newRemove = [];
		newCurrent.sort();
		this.setState({ current: newCurrent, remove: newRemove });
	}

	unAdd(value) {
		const add = new Set(this.state.add);
		add.delete(value);
		const newAdd = Array.from(add);
		newAdd.sort();
		if (this.getMapping().has(value)) {
			const current = new Set(this.state.current);
			current.add(value);
			const newCurrent = Array.from(current);
			newCurrent.sort();
			this.setState({ current: newCurrent, add: newAdd });
		} else {
			this.setState({ add: newAdd });
		}
	}

	unAddAll() {
		const current = new Set(this.state.current);
		for (let value of this.state.add) {
			if (this.getMapping().has(value)) {
				current.add(value);
			}
		}
		const newCurrent = Array.from(current);
		const newAdd = [];
		newCurrent.sort();
		this.setState({ current: newCurrent, add: newAdd });
	}

	onClose() {
		this.props.onClose({ add: this.state.add, remove: this.state.remove });
	}
}

FormSelectedVideosEditProperty.contextType = LangContext;
