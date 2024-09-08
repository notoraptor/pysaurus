import { ActionToCross } from "../components/ActionToCross.js";
import { ActionToMenuItem } from "../components/ActionToMenuItem.js";
import { ActionToSettingIcon } from "../components/ActionToSettingIcon.js";
import { Cell } from "../components/Cell.js";
import { Collapsable } from "../components/Collapsable.js";
import { Cross } from "../components/Cross.js";
import { GroupView } from "../components/GroupView.js";
import { Menu } from "../components/Menu.js";
import { MenuItem } from "../components/MenuItem.js";
import { MenuItemCheck } from "../components/MenuItemCheck.js";
import { MenuItemRadio } from "../components/MenuItemRadio.js";
import { MenuPack } from "../components/MenuPack.js";
import { Pagination } from "../components/Pagination.js";
import { Video } from "../components/Video.js";
import { Dialog } from "../dialogs/Dialog.js";
import { FancyBox } from "../dialogs/FancyBox.js";
import { FormDatabaseEditFolders } from "../forms/FormDatabaseEditFolders.js";
import { FormPropertyEditSelectedValues } from "../forms/FormPropertyEditSelectedValues.js";
import { FormSelectedVideosEditProperty } from "../forms/FormSelectedVideosEditProperty.js";
import { FormVideosGrouping } from "../forms/FormVideosGrouping.js";
import { FormVideosKeywordsToProperty } from "../forms/FormVideosKeywordsToProperty.js";
import { FormVideosSearch } from "../forms/FormVideosSearch.js";
import { FormVideosSort } from "../forms/FormVideosSort.js";
import { FormVideosSource } from "../forms/FormVideosSource.js";
import { GenericFormRename } from "../forms/GenericFormRename.js";
import { tr } from "../language.js";
import { Action } from "../utils/Action.js";
import { Actions } from "../utils/Actions.js";
import { backend_error, python_call, python_multiple_call } from "../utils/backend.js";
import { FIELD_MAP, PAGE_SIZES, SearchTypeTitle, SOURCE_TREE } from "../utils/constants.js";
import { Fancybox } from "../utils/FancyboxManager.js";
import { arrayEquals, compareSources } from "../utils/functions.js";
import { APP_STATE } from "../utils/globals.js";
import { Selector } from "../utils/Selector.js";
import { HomePage } from "./HomePage.js";

export class VideosPage extends React.Component {
	constructor(props) {
		// parameters: {backend state}
		// app: App
		super(props);

		this.state = this.parametersToState(
			{
				status: undefined,
				confirmDeletion: true,
				path: [],
				selector: new Selector(),
				displayOnlySelected: false,
				groupPageSize: 100,
				groupPageNumber: 0,
				groupSelection: new Set(),
			},
			this.props.parameters
		);
		this.backendGroupVideos = this.backendGroupVideos.bind(this);
		this.changeGroup = this.changeGroup.bind(this);
		this.changePage = this.changePage.bind(this);
		this.previousPage = this.previousPage.bind(this);
		this.nextPage = this.nextPage.bind(this);
		this.classifierConcatenate = this.classifierConcatenate.bind(this);
		this.classifierSelectGroup = this.classifierSelectGroup.bind(this);
		this.classifierUnstack = this.classifierUnstack.bind(this);
		this.classifierReversePath = this.classifierReversePath.bind(this);
		this.confirmDeletionForNotFound = this.confirmDeletionForNotFound.bind(this);
		this.deselect = this.deselect.bind(this);
		this.displayOnlySelected = this.displayOnlySelected.bind(this);
		this.editPropertiesForManyVideos = this.editPropertiesForManyVideos.bind(this);
		this.editPropertyValue = this.editPropertyValue.bind(this);
		this.fillWithKeywords = this.fillWithKeywords.bind(this);
		this.focusPropertyValue = this.focusPropertyValue.bind(this);
		this.groupVideos = this.groupVideos.bind(this);
		this.manageProperties = this.manageProperties.bind(this);
		this.onVideoSelection = this.onVideoSelection.bind(this);
		this.openRandomVideo = this.openRandomVideo.bind(this);
		this.reloadDatabase = this.reloadDatabase.bind(this);
		this.resetGroup = this.resetGroup.bind(this);
		this.resetSearch = this.resetSearch.bind(this);
		this.resetSort = this.resetSort.bind(this);
		this.resetStatus = this.resetStatus.bind(this);
		this.scrollTop = this.scrollTop.bind(this);
		this.searchVideos = this.searchVideos.bind(this);
		this.selectAll = this.selectAll.bind(this);
		this.selectGroup = this.selectGroup.bind(this);
		this.selectVideos = this.selectVideos.bind(this);
		this.setPageSize = this.setPageSize.bind(this);
		this.sortVideos = this.sortVideos.bind(this);
		this.unselectVideos = this.unselectVideos.bind(this);
		this.updateStatus = this.updateStatus.bind(this);
		this.backend = this.backend.bind(this);
		this.findSimilarVideos = this.findSimilarVideos.bind(this);
		this.closeDatabase = this.closeDatabase.bind(this);
		this.moveVideo = this.moveVideo.bind(this);
		this.editDatabaseFolders = this.editDatabaseFolders.bind(this);
		this.renameDatabase = this.renameDatabase.bind(this);
		this.deleteDatabase = this.deleteDatabase.bind(this);
		this.onGroupViewState = this.onGroupViewState.bind(this);
		this.notify = this.notify.bind(this);
		this.allNotFound = this.allNotFound.bind(this);
		this.canOpenRandomVideo = this.canOpenRandomVideo.bind(this);
		this.canFindSimilarVideos = this.canFindSimilarVideos.bind(this);
		this.sourceIsSet = this.sourceIsSet.bind(this);
		this.groupIsSet = this.groupIsSet.bind(this);
		this.searchIsSet = this.searchIsSet.bind(this);
		this.sortIsSet = this.sortIsSet.bind(this);
		this.previousGroup = this.previousGroup.bind(this);
		this.nextGroup = this.nextGroup.bind(this);
		this.confirmAllUniqueMoves = this.confirmAllUniqueMoves.bind(this);
		this.getStatus = this.getStatus.bind(this);
		this.getActions = this.getActions.bind(this);
		this.playlist = this.playlist.bind(this);

		this.callbackIndex = -1;
	}

	render() {
		const languages = this.props.app.getLanguages();
		const nbVideos = this.state.nbVideos;
		const nbPages = this.state.nbPages;
		const validSize = this.state.validSize;
		const validLength = this.state.validLength;
		const groupDef = this.state.groupDef;
		const groupedByMoves = groupDef && groupDef.field === "move_id";
		const stringSetProperties = this.getStringSetProperties(this.state.prop_types);
		const stringProperties = this.getStringProperties(this.state.prop_types);
		const actions = this.getActions().actions;
		const aFilterIsSet = this.sourceIsSet() || this.groupIsSet() || this.searchIsSet() || this.sortIsSet();
		const status = this.getStatus();

		return (
			<div id="videos" className="absolute-plain p-4 vertical">
				<header className="horizontal flex-shrink-0">
					<MenuPack title={tr("Database ...")}>
						<Menu title="Reload database ...">{<ActionToMenuItem action={actions.reload} />}</Menu>
						<MenuItem action={this.renameDatabase}>
							{tr('Rename database "{name}" ...', {
								name: this.state.database.name,
							})}
						</MenuItem>
						<MenuItem action={this.editDatabaseFolders}>
							{tr("Edit {count} database folders ...", {
								count: this.state.database.folders.length,
							})}
						</MenuItem>
						<Menu title={tr("Close database ...")}>
							<MenuItem action={this.closeDatabase}>
								<strong>{tr("Close database")}</strong>
							</MenuItem>
						</Menu>
						<MenuItem className="red-flag" action={this.deleteDatabase}>
							{tr("Delete database ...")}
						</MenuItem>
					</MenuPack>
					<MenuPack title={tr("Videos ...")}>
						<Menu title={tr("Filter videos ...")}>
							{<ActionToMenuItem action={actions.select} />}
							{<ActionToMenuItem action={actions.group} />}
							{<ActionToMenuItem action={actions.search} />}
							{<ActionToMenuItem action={actions.sort} />}
						</Menu>
						{aFilterIsSet ? (
							<Menu title={tr("Reset filters ...")}>
								{this.sourceIsSet() ? <ActionToMenuItem action={actions.unselect} /> : ""}
								{this.groupIsSet() ? <ActionToMenuItem action={actions.ungroup} /> : ""}
								{this.searchIsSet() ? <ActionToMenuItem action={actions.unsearch} /> : ""}
								{this.sortIsSet() ? <ActionToMenuItem action={actions.unsort} /> : ""}
							</Menu>
						) : (
							""
						)}
						{this.canOpenRandomVideo() ? <ActionToMenuItem action={actions.openRandomVideo} /> : ""}
						{this.canFindSimilarVideos() ? (
							<Menu title={tr("Search similar videos (may be long) ...")}>
								<MenuItem action={this.findSimilarVideos}>
									<strong>{tr("Find similar videos")}</strong>
								</MenuItem>
							</Menu>
						) : (
							""
						)}
						{groupedByMoves ? (
							<MenuItem action={this.confirmAllUniqueMoves}>
								<strong>
									<em>{tr("Confirm all unique moves")}</em>
								</strong>
							</MenuItem>
						) : (
							""
						)}
						<MenuItem action={this.playlist} shortcut="Ctrl+L">
							<strong>
								<em>Play list</em>
							</strong>
						</MenuItem>
					</MenuPack>
					<MenuPack title={tr("Properties ...")}>
						{<ActionToMenuItem action={actions.manageProperties} />}
						{stringSetProperties.length ? (
							<MenuItem action={this.fillWithKeywords}>{tr("Put keywords into a property ...")}</MenuItem>
						) : (
							""
						)}
						{this.state.prop_types.length > 5 ? (
							<Menu title={tr("Group videos by property ...")}>
								{this.state.prop_types.map((def, index) => (
									<MenuItem key={index} action={() => this.backendGroupVideos(def.name, true)}>
										{def.name}
									</MenuItem>
								))}
							</Menu>
						) : (
							this.state.prop_types.map((def, index) => (
								<MenuItem key={index} action={() => this.backendGroupVideos(def.name, true)}>
									{tr("Group videos by property: {name}", {
										name: def.name,
									})}
								</MenuItem>
							))
						)}
						{stringProperties.length ? (
							<Menu title={tr("Convert values to lowercase for ...")}>
								{stringProperties.map((def, defIndex) => (
									<MenuItem key={defIndex} action={() => this.propToLowercase(def)}>
										{def.name}
									</MenuItem>
								))}
							</Menu>
						) : (
							""
						)}
						{stringProperties.length ? (
							<Menu title={tr("Convert values to uppercase for ...")}>
								{stringProperties.map((def, defIndex) => (
									<MenuItem key={defIndex} action={() => this.propToUppercase(def)}>
										{def.name}
									</MenuItem>
								))}
							</Menu>
						) : (
							""
						)}
					</MenuPack>
					<MenuPack title={tr("Navigation ...")}>
						<Menu title={tr("Videos ...")}>
							<ActionToMenuItem action={actions.previousPage} />
							<ActionToMenuItem action={actions.nextPage} />
						</Menu>
						{this.groupIsSet() ? (
							<Menu title={tr("Groups ...")}>
								<MenuItem action={this.previousGroup} shortcut="Ctrl+ArrowUp">
									{tr("Go to previous group")}
								</MenuItem>
								<MenuItem action={this.nextGroup} shortcut="Ctrl+ArrowDown">
									{tr("Go to next group")}
								</MenuItem>
							</Menu>
						) : (
							""
						)}
					</MenuPack>
					<MenuPack title={tr("Options")}>
						<Menu title={tr("Page size ...")}>
							{PAGE_SIZES.map((count, index) => (
								<MenuItemRadio
									key={index}
									checked={this.state.pageSize === count}
									value={count}
									action={this.setPageSize}>
									{tr("{count} video(s) per page", {
										count,
									})}
								</MenuItemRadio>
							))}
						</Menu>
						<MenuItemCheck checked={this.state.confirmDeletion} action={this.confirmDeletionForNotFound}>
							{tr("confirm deletion for entries not found")}
						</MenuItemCheck>
						{languages.length > 1 ? (
							<Menu title={tr("Language:") + " ..."}>
								{languages.map((language, index) => (
									<MenuItem key={index} action={() => this.props.app.setLanguage(language)}>
										{window.PYTHON_LANGUAGE === language ? <strong>{language}</strong> : language}
									</MenuItem>
								))}
							</Menu>
						) : (
							""
						)}
					</MenuPack>
					<div className="pagination text-right">
						<Pagination
							singular={tr("page")}
							plural={tr("pages")}
							nbPages={nbPages}
							pageNumber={this.state.pageNumber}
							key={this.state.pageNumber}
							onChange={this.changePage}
						/>
					</div>
				</header>
				<div className="frontier block flex-shrink-0" />
				<div className="content position-relative flex-grow-1">
					<div className="absolute-plain horizontal">
						<div className="side-panel vertical">
							<Collapsable lite={false} className="filter flex-shrink-0" title={tr("Filter")}>
								{this.renderFilter()}
							</Collapsable>
							{this.state.path.length ? (
								<Collapsable
									lite={false}
									className="filter flex-shrink-0"
									title={tr("Classifier path")}>
									{stringProperties.length ? (
										<div className="path-menu text-center p-2">
											<MenuPack title={tr("Concatenate path into ...")}>
												{stringProperties.map((def, i) => (
													<MenuItem
														key={i}
														action={() => this.classifierConcatenate(def.name)}>
														{def.name}
													</MenuItem>
												))}
											</MenuPack>
											<div className="pt-2">
												<button className="block" onClick={this.classifierReversePath}>
													{tr("reverse path")}
												</button>
											</div>
										</div>
									) : (
										""
									)}
									{this.state.path.map((value, index) => (
										<div key={index} className="path-step horizontal px-2 py-1">
											<div className="flex-grow-1">{value.toString()}</div>
											{index === this.state.path.length - 1 ? (
												<div className="icon">
													<Cross title={tr("unstack")} action={this.classifierUnstack} />
												</div>
											) : (
												""
											)}
										</div>
									))}
								</Collapsable>
							) : (
								""
							)}
							{groupDef ? (
								<div className="flex-grow-1 position-relative">
									<Collapsable
										lite={false}
										className="group absolute-plain vertical"
										title={tr("Groups")}>
										<GroupView
											groupDef={groupDef}
											isClassified={!!this.state.path.length}
											pageSize={this.state.groupPageSize}
											pageNumber={this.state.groupPageNumber}
											selection={this.state.groupSelection}
											onGroupViewState={this.onGroupViewState}
											onOptions={this.editPropertyValue}
											onPlus={
												groupDef.is_property && this.state.definitions[groupDef.field].multiple
													? this.classifierSelectGroup
													: null
											}
										/>
									</Collapsable>
								</div>
							) : (
								""
							)}
						</div>
						<div className="main-panel videos overflow-auto">
							{this.state.videos.map((data) => (
								<Video
									key={data.video_id}
									data={data}
									propDefs={this.state.prop_types}
									groupDef={groupDef}
									selected={this.state.selector.has(data.video_id)}
									onSelect={this.onVideoSelection}
									onMove={this.moveVideo}
									onSelectPropertyValue={this.focusPropertyValue}
									onInfo={this.updateStatus}
									confirmDeletion={this.state.confirmDeletion}
									groupedByMoves={groupedByMoves}
								/>
							))}
						</div>
					</div>
				</div>
				<footer className="horizontal flex-shrink-0">
					<div className="footer-status clickable" title={status} onClick={this.resetStatus}>
						{status}
					</div>
					<div className="footer-information text-right">
						{groupDef ? (
							<div className="info group">
								{groupDef.groups.length
									? tr("Group {group}/{count}", {
											group: groupDef.group_id + 1,
											count: groupDef.groups.length,
									  })
									: tr("No groups")}
							</div>
						) : (
							""
						)}
						<div className="info count">
							{nbVideos} video{nbVideos > 1 ? "s" : ""}
						</div>
						<div className="info size">{validSize}</div>
						<div className="info length">{validLength}</div>
					</div>
				</footer>
			</div>
		);
	}

	renderFilter() {
		const actions = this.getActions().actions;
		const sources = this.state.sources;
		const groupDef = this.state.groupDef;
		const searchDef = this.state.searchDef;
		const sorting = this.state.sorting;
		const nbViewVideos = this.state.nbViewVideos;
		const selectionSize = this.state.selector.size(nbViewVideos);
		const sortingIsDefault = sorting.length === 1 && sorting[0] === "-date";
		const selectedAll = nbViewVideos === selectionSize;
		return (
			<table className="filter w-100">
				<tbody>
					{/** Sources **/}
					<tr>
						<td>
							{sources.map((source, index) => (
								<div key={index}>{source.join(" ").replace("_", " ")}</div>
							))}
						</td>
						<td>
							<div>
								<ActionToSettingIcon action={actions.select} />
							</div>
							{this.sourceIsSet() ? (
								<div>
									<ActionToCross action={actions.unselect} />
								</div>
							) : (
								""
							)}
						</td>
					</tr>
					{/** Grouping **/}
					<tr>
						<td>
							{groupDef ? <div>{tr("Grouped")}</div> : <div className="no-filter">{tr("Ungrouped")}</div>}
						</td>
						<td>
							<div>
								<ActionToSettingIcon
									action={actions.group}
									title={groupDef ? tr("Edit ...") : tr("Group ...")}
								/>
							</div>
							{groupDef ? (
								<div>
									<ActionToCross action={actions.ungroup} />
								</div>
							) : (
								""
							)}
						</td>
					</tr>
					{/** Search **/}
					<tr>
						<td>
							{searchDef ? (
								<div>
									<div>
										{tr("Searched {text}", {
											text: SearchTypeTitle[searchDef.cond],
										})}
									</div>
									<div className="word-break-all">
										&quot;<strong>{searchDef.text}</strong>
										&quot;
									</div>
								</div>
							) : (
								<div className="no-filter">{tr("No search")}</div>
							)}
						</td>
						<td>
							<div>
								<ActionToSettingIcon
									action={actions.search}
									title={searchDef ? tr("Edit ...") : tr("Search ...")}
								/>
							</div>
							{searchDef ? (
								<div>
									<ActionToCross action={actions.unsearch} />
								</div>
							) : (
								""
							)}
						</td>
					</tr>
					{/** Sort **/}
					<tr>
						<td>
							<div>{tr("Sorted by")}</div>
							{sorting.map((val, i) => (
								<div key={i}>
									<strong>{FIELD_MAP.fields[val.substring(1)].title}</strong>{" "}
									{val[0] === "-" ? <span>&#9660;</span> : <span>&#9650;</span>}
								</div>
							))}
						</td>
						<td>
							<div>
								<ActionToSettingIcon action={actions.sort} />
							</div>
							{sortingIsDefault ? (
								""
							) : (
								<div>
									<ActionToCross action={actions.unsort} />
								</div>
							)}
						</td>
					</tr>
					{/** Selection **/}
					<tr>
						<td>
							{selectionSize ? (
								<div>
									<div>Selected</div>
									<div>
										{selectedAll
											? tr("All {count} video(s)", {
													count: selectionSize,
											  })
											: tr("{count} / {total} video(s)", {
													count: selectionSize,
													total: nbViewVideos,
											  })}
									</div>
									<div className="mb-1">
										<button onClick={this.displayOnlySelected}>
											{this.state.displayOnlySelected
												? tr("Display all videos")
												: tr("Display only selected videos")}
										</button>
									</div>
								</div>
							) : (
								<div>{tr("No videos selected")}</div>
							)}
							{selectedAll ? (
								""
							) : (
								<div className="mb-1">
									<button onClick={this.selectAll}>{tr("select all")}</button>
								</div>
							)}
							{selectionSize ? (
								<div className="mb-1">
									<MenuPack title={tr("Edit property ...")}>
										{this.state.prop_types.map((def, index) => (
											<MenuItem
												key={index}
												action={() => this.editPropertiesForManyVideos(def.name)}>
												{def.name}
											</MenuItem>
										))}
									</MenuPack>
								</div>
							) : (
								""
							)}
						</td>
						<td>{selectionSize ? <Cross title={tr("Deselect all")} action={this.deselect} /> : ""}</td>
					</tr>
				</tbody>
			</table>
		);
	}

	getStatus() {
		return this.state.status === undefined ? tr("Loaded.") : this.state.status;
	}

	getActions() {
		// 14 shortcuts currently.
		return new Actions({
			select: new Action("Ctrl+T", tr("Select videos ..."), this.selectVideos, Fancybox.isInactive),
			group: new Action("Ctrl+G", tr("Group ..."), this.groupVideos, Fancybox.isInactive),
			search: new Action("Ctrl+F", tr("Search ..."), this.searchVideos, Fancybox.isInactive),
			sort: new Action("Ctrl+S", tr("Sort ..."), this.sortVideos, Fancybox.isInactive),
			unselect: new Action("Ctrl+Shift+T", tr("Reset selection"), this.unselectVideos, Fancybox.isInactive),
			ungroup: new Action("Ctrl+Shift+G", tr("Reset group"), this.resetGroup, Fancybox.isInactive),
			unsearch: new Action("Ctrl+Shift+F", tr("Reset search"), this.resetSearch, Fancybox.isInactive),
			unsort: new Action("Ctrl+Shift+S", tr("Reset sorting"), this.resetSort, Fancybox.isInactive),
			reload: new Action("Ctrl+R", tr("Reload database ..."), this.reloadDatabase, Fancybox.isInactive),
			manageProperties: new Action(
				"Ctrl+P",
				tr("Manage properties ..."),
				this.manageProperties,
				Fancybox.isInactive
			),
			openRandomVideo: new Action(
				"Ctrl+O",
				tr("Open random video"),
				this.openRandomVideo,
				this.canOpenRandomVideo
			),
			previousPage: new Action(
				"Ctrl+ArrowLeft",
				tr("Go to previous page"),
				this.previousPage,
				Fancybox.isInactive
			),
			nextPage: new Action("Ctrl+ArrowRight", tr("Go to next page"), this.nextPage, Fancybox.isInactive),
			playlist: new Action("Ctrl+L", tr("play list"), this.playlist, Fancybox.isInactive),
		});
	}

	sourceIsSet() {
		return !compareSources(window.PYTHON_DEFAULT_SOURCES, this.state.sources);
	}

	groupIsSet() {
		return !!this.state.groupDef;
	}

	searchIsSet() {
		return !!this.state.searchDef;
	}

	sortIsSet() {
		return !(this.state.sorting.length === 1 && this.state.sorting[0] === "-date");
	}

	allNotFound() {
		for (let source of this.state.sources) {
			if (source.indexOf("not_found") < 0) return false;
		}
		return true;
	}

	canOpenRandomVideo() {
		return Fancybox.isInactive() && !this.allNotFound() && this.state.nbSourceVideos;
	}

	canFindSimilarVideos() {
		return window.PYTHON_FEATURE_COMPARISON;
	}

	componentDidMount() {
		this.callbackIndex = KEYBOARD_MANAGER.register(this.getActions().onKeyPressed);
		NOTIFICATION_MANAGER.installFrom(this);
	}

	componentWillUnmount() {
		KEYBOARD_MANAGER.unregister(this.callbackIndex);
		NOTIFICATION_MANAGER.uninstallFrom(this);
	}

	/**
	 * @param state {Object}
	 * @param field {String}
	 * @returns {*}
	 */
	getStateField(state, field) {
		return state[field] === undefined ? (this.state === undefined ? undefined : this.state[field]) : state[field];
	}

	backend(callargs, state = {}, top = true) {
		const pageSize = this.getStateField(state, "pageSize");
		const pageNumber = this.getStateField(state, "pageNumber");
		const displayOnlySelected = this.getStateField(state, "displayOnlySelected");
		const selector = displayOnlySelected ? this.getStateField(state, "selector").toJSON() : null;
		if (!state.status) state.status = tr("updated.");
		const run = async () => {
			if (callargs) await python_call(...callargs);
			return await python_call("backend", pageSize, pageNumber, selector);
		};
		run()
			.then((info) => this.setState(this.parametersToState(state, info), top ? this.scrollTop : undefined))
			.catch(backend_error);
	}

	viewHasChanged(state, info) {
		const prevSources = this.getStateField(state, "sources") || window.PYTHON_DEFAULT_SOURCES;
		const nextSources = info.sources || [];
		if (!compareSources(prevSources, nextSources)) return true;
		const prevGroupDef = this.getStateField(state, "groupDef") || {};
		const nextGroupDef = info.groupDef || {};
		for (let field of ["field", "is_property", "sorting", "reverse", "allow_singletons", "group_id"]) {
			if (prevGroupDef[field] !== nextGroupDef[field]) return true;
		}
		const prevPath = this.getStateField(state, "path") || [];
		const nextPath = info.path || [];
		if (prevPath.length !== nextPath.length) return true;
		for (let i = 0; i < prevPath.length; ++i) {
			if (prevPath[i] !== nextPath[i]) return true;
		}
		const prevSearchDef = this.getStateField(state, "searchDef") || {};
		const nextSearchDef = info.searchDef || {};
		return prevSearchDef.text !== nextSearchDef.text || prevSearchDef.cond !== nextSearchDef.cond;
	}

	parametersToState(state, info) {
		if (info.groupDef) {
			const groupPageSize = this.getStateField(state, "groupPageSize");
			const groupPageNumber = this.getStateField(state, "groupPageNumber");
			const count = info.groupDef.groups.length;
			const nbPages = Math.floor(count / groupPageSize) + (count % groupPageSize ? 1 : 0);
			state.groupPageNumber = Math.min(Math.max(0, groupPageNumber), nbPages - 1);
		}
		const viewChanged = this.viewHasChanged(state, info);
		console.log(`View changed? ${viewChanged ? "true" : "false"}`);
		if (viewChanged) state.selector = new Selector();
		const definitions = {};
		for (let propType of info.prop_types) {
			definitions[propType.name] = propType;
		}
		state.definitions = definitions;
		return Object.assign(state, info);
	}

	notify(notification) {
		if (notification.name === "NextRandomVideo") this.backend(null, {});
	}

	onGroupViewState(groupState) {
		const state = {};
		if (groupState.hasOwnProperty("pageSize")) state.groupPageSize = groupState.pageSize;
		if (groupState.hasOwnProperty("pageNumber")) state.groupPageNumber = groupState.pageNumber;
		if (groupState.hasOwnProperty("selection")) state.groupSelection = groupState.selection;
		const groupID = groupState.hasOwnProperty("groupID") ? groupState.groupID : null;
		this.setState(state, groupID === null ? undefined : () => this.selectGroup(groupID));
	}

	scrollTop() {
		document.querySelector("#videos .videos").scrollTop = 0;
	}

	onVideoSelection(videoID, selected) {
		const selector = this.state.selector.clone();
		if (selected) {
			selector.add(videoID);
			this.setState({ selector });
		} else {
			selector.remove(videoID);
			if (this.state.displayOnlySelected)
				this.backend(null, {
					selector,
					displayOnlySelected: this.state.displayOnlySelected && selector.size(this.state.nbViewVideos),
				});
			else this.setState({ selector });
		}
	}

	moveVideo(videoID, directory) {
		Fancybox.load(
			<FancyBox
				title={tr("Move file to {path}", {
					path: directory,
				})}
				onClose={() => {
					python_call("cancel_copy");
				}}>
				<div className="absolute-plain vertical">
					<HomePage
						key={APP_STATE.idGenerator.next()}
						app={this.props.app}
						parameters={{
							command: ["move_video_file", videoID, directory],
							onReady: (status) => {
								Fancybox.close();
								if (status === "Cancelled") this.updateStatus(tr("Video not moved."));
								else
									this.updateStatus(
										tr("Video moved to {directory}", {
											directory,
										}),
										true
									);
							},
						}}
					/>
				</div>
			</FancyBox>
		);
	}

	deselect() {
		const selector = this.state.selector.clone();
		selector.clear();
		if (this.state.displayOnlySelected) this.backend(null, { selector, displayOnlySelected: false });
		else this.setState({ selector });
	}

	selectAll() {
		// Should not be called if displayOnlySelected is true.
		const selector = this.state.selector.clone();
		selector.fill();
		if (this.state.displayOnlySelected) this.backend(null, { selector });
		else this.setState({ selector });
	}

	displayOnlySelected() {
		this.backend(null, {
			displayOnlySelected: !this.state.displayOnlySelected,
		});
	}

	updateStatus(status, reload = false, top = false) {
		if (reload) this.backend(null, { status }, top);
		else this.setState({ status });
	}

	resetStatus() {
		this.setState({ status: tr("Ready.") });
	}

	unselectVideos() {
		this.backend(["set_sources", null], { pageNumber: 0 });
	}

	selectVideos() {
		Fancybox.load(
			<FormVideosSource
				tree={SOURCE_TREE}
				sources={this.state.sources}
				onClose={(sources) => {
					this.backend(["set_sources", sources], { pageNumber: 0 });
				}}
			/>
		);
	}

	groupVideos() {
		const groupDef = this.state.groupDef || {
			field: null,
			is_property: null,
			reverse: null,
		};
		Fancybox.load(
			<FormVideosGrouping
				groupDef={groupDef}
				prop_types={this.state.prop_types}
				propertyMap={this.state.definitions}
				onClose={(criterion) => {
					this.backend(
						[
							"set_groups",
							criterion.field,
							criterion.isProperty,
							criterion.sorting,
							criterion.reverse,
							criterion.allowSingletons,
						],
						{ pageNumber: 0 }
					);
				}}
			/>
		);
	}

	backendGroupVideos(field, isProperty = false, sorting = "count", reverse = true, allowSingletons = true) {
		this.backend(["set_groups", field, isProperty, sorting, reverse, allowSingletons], {
			pageNumber: 0,
		});
	}

	editPropertiesForManyVideos(propertyName) {
		const selectionSize = this.state.selector.size(this.state.nbViewVideos);
		const videoIndices = this.state.selector.toJSON();
		python_call("apply_on_view", videoIndices, "count_property_values", propertyName)
			.then((valuesAndCounts) => {
				Fancybox.load(
					<FormSelectedVideosEditProperty
						nbVideos={selectionSize}
						definition={this.state.definitions[propertyName]}
						values={valuesAndCounts}
						onClose={(edition) => {
							this.backend(
								[
									"apply_on_view",
									videoIndices,
									"edit_property_for_videos",
									propertyName,
									edition.add,
									edition.remove,
								],
								{
									pageNumber: 0,
									status: tr("Edited property {property} for {count} video(s).", {
										property: propertyName,
										count: selectionSize,
									}),
								}
							);
						}}
					/>
				);
			})
			.catch(backend_error);
	}

	searchVideos() {
		const search_def = this.state.searchDef || { text: null, cond: null };
		Fancybox.load(
			<FormVideosSearch
				text={search_def.text}
				cond={search_def.cond}
				onClose={(criterion) => {
					this.backend(["set_search", criterion.text, criterion.cond], {
						pageNumber: 0,
					});
				}}
			/>
		);
	}

	sortVideos() {
		Fancybox.load(
			<FormVideosSort
				sorting={this.state.sorting}
				onClose={(sorting) => {
					this.backend(["set_sorting", sorting], { pageNumber: 0 });
				}}
			/>
		);
	}

	editDatabaseFolders() {
		Fancybox.load(
			<FormDatabaseEditFolders
				database={this.state.database}
				onClose={(paths) => {
					python_call("set_video_folders", paths)
						.then(() => this.props.app.dbUpdate("update_database"))
						.catch(backend_error);
				}}
			/>
		);
	}

	renameDatabase() {
		const name = this.state.database.name;
		Fancybox.load(
			<GenericFormRename
				title={tr('Rename database "{name}"', { name })}
				header={tr("Rename database")}
				description={name}
				data={name}
				onClose={(name) => {
					this.backend(["rename_database", name], { pageNumber: 0 });
				}}
			/>
		);
	}

	deleteDatabase() {
		Fancybox.load(
			<Dialog
				title={tr("Delete database {name}", {
					name: this.state.database.name,
				})}
				yes={tr("DELETE")}
				action={() => {
					python_multiple_call(["delete_database"], ["get_database_names"])
						.then((database_names) => this.props.app.dbHome({ database_names }))
						.catch(backend_error);
				}}>
				<Cell center={true} full={true} className="text-center">
					<h1>
						{tr("Database")} <span className="red-flag">{this.state.database.name}</span>
					</h1>
					{tr(
						`
## Are you sure you want to delete this database?

### Database entries and thumbnails will be deleted.

### Video files won't be touched.
`,
						null,
						"markdown"
					)}
				</Cell>
			</Dialog>
		);
	}

	confirmAllUniqueMoves() {
		Fancybox.load(
			<Dialog
				title={tr("Confirm all unique moves")}
				yes={tr("move")}
				action={() => {
					python_call("confirm_unique_moves")
						.then((nbMoved) => this.updateStatus(`Moved ${nbMoved} video(s)`, true, true))
						.catch(backend_error);
				}}>
				<Cell center={true} full={true} className="text-center">
					{tr(
						`
# Are you sure you want to confirm all unique moves?

## Each not found video which has one unique other found video with

same size and duration will be moved to the later.

Properties and variable attributes will be copied

from not found to found video, and

not found video entry will be deleted.
`,
						null,
						"markdown"
					)}
				</Cell>
			</Dialog>
		);
	}

	resetGroup() {
		this.backend(["set_groups", ""], { pageNumber: 0 });
	}

	resetSearch() {
		this.backend(["set_search", null, null], { pageNumber: 0 });
	}

	resetSort() {
		this.backend(["set_sorting", null], { pageNumber: 0 });
	}

	openRandomVideo() {
		python_call("open_random_video")
			.then((filename) => {
				APP_STATE.videoHistory.add(filename);
				this.updateStatus(
					tr("Randomly opened: {path}", {
						path: filename,
					}),
					true,
					true
				);
			})
			.catch(backend_error);
	}

	playlist() {
		python_call("playlist")
			.then((filename) => this.updateStatus(`Opened playlist: ${filename}`))
			.catch(backend_error);
	}

	reloadDatabase() {
		this.props.app.dbUpdate("update_database");
	}

	findSimilarVideos() {
		this.props.app.dbUpdate("find_similar_videos");
	}

	manageProperties() {
		this.props.app.loadPropertiesPage();
	}

	fillWithKeywords() {
		Fancybox.load(
			<FormVideosKeywordsToProperty
				prop_types={this.getStringSetProperties(this.state.prop_types)}
				onClose={(state) => {
					python_call("fill_property_with_terms", state.field, state.onlyEmpty)
						.then(() =>
							this.updateStatus(
								tr('Filled property "{name}" with video keywords.', {
									name: state.field,
								}),
								true
							)
						)
						.catch(backend_error);
				}}
			/>
		);
	}

	setPageSize(count) {
		if (count !== this.state.pageSize) this.backend(null, { pageSize: count, pageNumber: 0 });
	}

	confirmDeletionForNotFound(checked) {
		this.setState({ confirmDeletion: checked });
	}

	changeGroup(groupNumber) {
		this.backend(["set_group", groupNumber], { pageNumber: 0 });
	}

	selectGroup(value) {
		if (value === -1) this.resetGroup();
		else this.changeGroup(value);
	}

	changePage(pageNumber) {
		this.backend(null, { pageNumber });
	}

	previousPage() {
		const pageNumber = this.state.pageNumber - 1;
		if (pageNumber >= 0) this.changePage(pageNumber);
	}

	nextPage() {
		const pageNumber = this.state.pageNumber + 1;
		if (pageNumber < this.state.nbPages) this.changePage(pageNumber);
	}

	previousGroup() {
		const groupID = this.state.groupDef.group_id;
		if (groupID > 0) this.onGroupViewState({ groupID: groupID - 1 });
	}

	nextGroup() {
		const groupID = this.state.groupDef.group_id;
		if (groupID < this.state.groupDef.groups.length - 1) this.onGroupViewState({ groupID: groupID + 1 });
	}

	getStringSetProperties(definitions) {
		return definitions.filter((def) => def.multiple && def.type === "str");
	}

	getStringProperties(definitions) {
		return definitions.filter((def) => def.type === "str");
	}

	/**
	 * @param indicesSet {Set}
	 */
	editPropertyValue(indicesSet) {
		const groupDef = this.state.groupDef;
		const name = groupDef.field;
		const values = [];
		const indices = Array.from(indicesSet);
		indices.sort();
		for (let index of indices) values.push(groupDef.groups[index].value);
		Fancybox.load(
			<FormPropertyEditSelectedValues
				definitions={this.state.definitions}
				name={name}
				values={values}
				onClose={(operation) => {
					switch (operation.form) {
						case "delete":
							this.backend(["delete_property_value", name, values], {
								groupSelection: new Set(),
								status: tr('Property value deleted: "{name}" : "{values}"', {
									name: name,
									values: values.join('", "'),
								}),
							});
							break;
						case "edit":
							this.backend(["edit_property_value", name, values, operation.value], {
								groupSelection: new Set(),
								status: tr('Property value edited: "{name}" : "{values}" -> "{destination}"', {
									name: name,
									values: values.join('", "'),
									destination: operation.value,
								}),
							});
							break;
						case "move":
							this.backend(["move_property_value", name, values, operation.move], {
								groupSelection: new Set(),
								status: tr('Property value moved: "{values}" from "{name}" to "{destination}"', {
									values: values.join('", "'),
									name: name,
									destination: operation.move,
								}),
							});
							break;
					}
				}}
			/>
		);
	}

	classifierReversePath() {
		python_call("classifier_reverse")
			.then((path) => this.setState({ path }))
			.catch(backend_error);
	}

	classifierSelectGroup(index) {
		this.backend(["classifier_select_group", index], { pageNumber: 0 });
	}

	classifierUnstack() {
		this.backend(["classifier_back"], { pageNumber: 0 });
	}

	classifierConcatenate(outputPropertyName) {
		this.backend(["classifier_concatenate_path", outputPropertyName], {
			pageNumber: 0,
		});
	}

	propToLowercase(def) {
		this.backend(["prop_to_lowercase", def.name]);
	}

	propToUppercase(def) {
		this.backend(["prop_to_uppercase", def.name]);
	}

	focusPropertyValue(propertyName, propertyValue) {
		this.backend(["classifier_focus_prop_val", propertyName, propertyValue], {
			pageNumber: 0,
		});
	}

	closeDatabase() {
		python_multiple_call(["close_database"], ["get_database_names"])
			.then((database_names) => this.props.app.dbHome({ database_names }))
			.catch(backend_error);
	}
}
