import { BaseComponent } from "../BaseComponent.js";
import { tr } from "../language.js";
import { Action } from "../utils/Action.js";
import { Actions } from "../utils/Actions.js";
import { Fancybox } from "../utils/FancyboxManager.js";
import { Characters, FIELD_MAP } from "../utils/constants.js";
import { capitalizeFirstLetter } from "../utils/functions.js";
import { Pagination } from "./Pagination.js";
import { PlusIcon } from "./PlusIcon.js";
import { SettingIcon } from "./SettingIcon.js";

export class GroupView extends BaseComponent {
	constructor(props) {
		super(props);
		this.callbackIndex = -1;
	}

	render() {
		const selection = this.props.selection;
		const selected = this.props.groupDef.group_id;
		const isProperty = this.props.groupDef.is_property;
		const start = this.props.pageSize * this.props.pageNumber;
		const end = Math.min(start + this.props.pageSize, this.props.groupDef.groups.length);
		const allChecked = this.allChecked(start, end);
		return (
			<div className="group-view absolute-plain vertical">
				<div className="header flex-shrink-0 text-center pt-2">
					<div className="title pb-2">
						<strong>{this.renderTitle()}</strong>
					</div>
					<div>
						<Pagination
							singular="page"
							plural="pages"
							nbPages={this.getNbPages()}
							pageNumber={this.props.pageNumber}
							onChange={this.setPage}
							onSearch={this.search}
						/>
					</div>
					{isProperty && !this.props.isClassified ? (
						<div className="selection line flex-shrink-0 horizontal">
							<div className="column">
								<input
									id="group-view-select-all"
									type="checkbox"
									checked={allChecked}
									onChange={(event) => this.onCheckAll(event, start, end)}
								/>{" "}
								<label htmlFor="group-view-select-all">
									{allChecked
										? tr("All {count} selected", {
												count: selection.size,
										  })
										: tr("{count} selected", {
												count: selection.size,
										  })}
								</label>
								{selection.size ? (
									<span>
										&nbsp;
										<SettingIcon
											key="options-for-selected"
											title="Options for selected..."
											action={this.openPropertyOptionsAll}
										/>
									</span>
								) : (
									""
								)}
							</div>
						</div>
					) : (
						""
					)}
				</div>
				<div className="content position-relative flex-grow-1 overflow-auto">
					{this.props.groupDef.groups.length ? (
						<table className="second-td-text-right w-100 table-layout-fixed">
							<tbody>
								{this.props.groupDef.groups.slice(start, end).map((entry, index) => {
									index = start + index;
									const buttons = [];
									if (isProperty && entry.value !== null) {
										if (!this.props.isClassified) {
											buttons.push(
												<input
													key="check-group"
													type="checkbox"
													checked={selection.has(index)}
													onChange={(event) => this.onCheckEntry(event, index)}
												/>
											);
											buttons.push(" ");
											if (!selection.size) {
												buttons.push(
													<SettingIcon
														key="options"
														title="Options ..."
														action={(event) => this.openPropertyOptions(event, index)}
													/>
												);
												buttons.push(" ");
											}
										}
										if (!selection.size) {
											buttons.push(
												<PlusIcon
													key="add"
													title="Add ..."
													action={(event) => this.openPropertyPlus(event, index)}
												/>
											);
											buttons.push(" ");
										}
									}
									const classes = [isProperty ? "property" : "attribute"];
									classes.push("clickable");
									if (selected === index) {
										classes.push("selected");
										classes.push("bold");
									}
									if (entry.value === null) {
										classes.push("all");
										classes.push("bolder");
									}
									return (
										<tr
											className={classes.join(" ")}
											key={index}
											onClick={() =>
												this.props.onGroupViewState({
													groupID: index,
												})
											}>
											<td {...(isProperty ? {} : { title: entry.value })}>
												{buttons}
												<span key="value" {...(isProperty ? { title: entry.value } : {})}>
													{entry.value === null ? "(none)" : entry.value}
												</span>
											</td>
											<td title={entry.count}>{entry.count}</td>
										</tr>
									);
								})}
							</tbody>
						</table>
					) : (
						<div className="absolute-plain no-groups text-center vertical">
							<strong>
								<em>{tr("No groups")}</em>
							</strong>
						</div>
					)}
				</div>
			</div>
		);
	}

	renderTitle() {
		const field = this.props.groupDef.field;
		let title = this.props.groupDef.is_property
			? `"${capitalizeFirstLetter(field)}"`
			: capitalizeFirstLetter(FIELD_MAP.fields[field].title);
		if (this.props.groupDef.sorting === "length") title = `|| ${title} ||`;
		else if (this.props.groupDef.sorting === "count") title = `${title} (#)`;
		title = `${title} ${this.props.groupDef.reverse ? Characters.ARROW_DOWN : Characters.ARROW_UP}`;
		return title;
	}

	componentDidMount() {
		this.callbackIndex = KEYBOARD_MANAGER.register(this.getActions().onKeyPressed);
	}

	componentWillUnmount() {
		KEYBOARD_MANAGER.unregister(this.callbackIndex);
	}

	getActions() {
		return new Actions({
			previous: new Action("Ctrl+ArrowUp", tr("Go to previous group"), this.previousGroup, Fancybox.isInactive),
			next: new Action("Ctrl+ArrowDown", tr("Go to next group"), this.nextGroup, Fancybox.isInactive),
		});
	}

	getNullIndex() {
		return this.props.groupDef.groups.length && this.props.groupDef.groups[0].value === null ? 0 : -1;
	}

	getNbPages() {
		const count = this.props.groupDef.groups.length;
		return Math.floor(count / this.props.pageSize) + (count % this.props.pageSize ? 1 : 0);
	}

	openPropertyOptions(event, index) {
		event.cancelBubble = true;
		event.stopPropagation();
		this.props.onOptions(new Set([index]));
	}

	openPropertyOptionsAll() {
		this.props.onOptions(this.props.selection);
	}

	openPropertyPlus(event, index) {
		event.cancelBubble = true;
		event.stopPropagation();
		if (this.props.onPlus) this.props.onPlus(index);
	}

	setPage(pageNumber) {
		if (this.props.pageNumber !== pageNumber)
			this.props.onGroupViewState({
				pageNumber: pageNumber,
				selection: new Set(),
			});
	}

	previousGroup() {
		const groupID = this.props.groupDef.group_id;
		if (groupID > 0) this.props.onGroupViewState({ groupID: groupID - 1 });
	}

	nextGroup() {
		const groupID = this.props.groupDef.group_id;
		if (groupID < this.props.groupDef.groups.length - 1) this.props.onGroupViewState({ groupID: groupID + 1 });
	}

	search(text) {
		for (let index = 0; index < this.props.groupDef.groups.length; ++index) {
			const value = this.props.groupDef.groups[index].value;
			if (value === null) continue;
			if (value.toString().toLowerCase().indexOf(text.trim().toLowerCase()) !== 0) continue;
			const pageNumber = Math.floor(index / this.props.pageSize);
			if (this.props.pageNumber !== pageNumber)
				this.props.onGroupViewState({
					pageNumber: pageNumber,
					selection: new Set(),
					groupID: index,
				});
			return;
		}
	}

	allChecked(start, end) {
		const nullGroupIndex = this.getNullIndex();
		for (let i = start; i < end; ++i) {
			if (!this.props.selection.has(i) && i !== nullGroupIndex) return false;
		}
		return true;
	}

	onCheckEntry(event, index) {
		const selection = new Set(this.props.selection);
		if (event.target.checked) {
			selection.add(index);
		} else {
			selection.delete(index);
		}
		this.props.onGroupViewState({ selection });
	}

	onCheckAll(event, start, end) {
		const selection = new Set(this.props.selection);
		if (event.target.checked) {
			for (let i = start; i < end; ++i) {
				selection.add(i);
			}
		} else {
			for (let i = start; i < end; ++i) {
				selection.delete(i);
			}
		}
		selection.delete(this.getNullIndex());
		this.props.onGroupViewState({ selection });
	}
}

GroupView.propTypes = {
	groupDef: PropTypes.shape({
		group_id: PropTypes.number.isRequired,
		field: PropTypes.string.isRequired,
		is_property: PropTypes.bool.isRequired,
		sorting: PropTypes.string.isRequired,
		reverse: PropTypes.bool.isRequired,
		groups: PropTypes.arrayOf(PropTypes.shape({ value: PropTypes.any, count: PropTypes.number })).isRequired,
	}).isRequired,
	isClassified: PropTypes.bool.isRequired,
	// onOptions(index)
	onOptions: PropTypes.func.isRequired,
	// onPlus(index)
	onPlus: PropTypes.func,
	// state
	pageSize: PropTypes.number.isRequired,
	pageNumber: PropTypes.number.isRequired,
	selection: PropTypes.instanceOf(Set).isRequired,
	// state change
	onGroupViewState: PropTypes.func.isRequired, // onGroupViewState({pageSize?, pageNumber?, selection?, groupID? => onSelect})
};
