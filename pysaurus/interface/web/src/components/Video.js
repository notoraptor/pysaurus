import { Dialog } from "../dialogs/Dialog.js";
import { FormVideoEditProperties } from "../forms/FormVideoEditProperties.js";
import { GenericFormRename } from "../forms/GenericFormRename.js";
import { tr } from "../language.js";
import { Fancybox } from "../utils/FancyboxManager.js";
import { backend_error, python_call } from "../utils/backend.js";
import { Characters } from "../utils/constants.js";
import { APP_STATE } from "../utils/globals.js";
import { Collapsable } from "./Collapsable.js";
import { Menu } from "./Menu.js";
import { MenuItem } from "./MenuItem.js";
import { MenuPack } from "./MenuPack.js";

/**
 * Generate class name for common value of videos grouped by similarity
 * @param value {boolean?}
 * @returns {string}
 */
function cc(value) {
	return value === undefined ? "" : value ? "common-true" : "common-false";
}

export class Video extends React.Component {
	constructor(props) {
		super(props);
		this.markAsRead = this.markAsRead.bind(this);
		this.openVideo = this.openVideo.bind(this);
		this.openVideoSurely = this.openVideoSurely.bind(this);
		this.confirmDeletion = this.confirmDeletion.bind(this);
		this.deleteVideo = this.deleteVideo.bind(this);
		this.deleteVideoEntry = this.deleteVideoEntry.bind(this);
		this.openContainingFolder = this.openContainingFolder.bind(this);
		this.copyToClipboard = this.copyToClipboard.bind(this);
		this.copyMetaTitle = this.copyMetaTitle.bind(this);
		this.copyFileTitle = this.copyFileTitle.bind(this);
		this.copyFilePath = this.copyFilePath.bind(this);
		this.copyVideoID = this.copyVideoID.bind(this);
		this.renameVideo = this.renameVideo.bind(this);
		this.editProperties = this.editProperties.bind(this);
		this.onSelect = this.onSelect.bind(this);
		this.reallyDeleteVideo = this.reallyDeleteVideo.bind(this);
		this.reallyDeleteVideoEntry = this.reallyDeleteVideoEntry.bind(this);
		this.confirmMove = this.confirmMove.bind(this);
		this.moveVideo = this.moveVideo.bind(this);
		this.dismissSimilarity = this.dismissSimilarity.bind(this);
		this.reallyDismissSimilarity = this.reallyDismissSimilarity.bind(this);
		this.resetSimilarity = this.resetSimilarity.bind(this);
		this.reallyResetSimilarity = this.reallyResetSimilarity.bind(this);
	}

	render() {
		return this.props.data.readable ? this.renderVideo() : this.renderVideoState();
	}

	renderVideo() {
		const data = this.props.data;
		const audio_bit_rate = Math.round(data.audio_bit_rate / 1000);
		data.extension = data.extension.toUpperCase();
		data.frame_rate = Math.round(data.frame_rate);
		const title = data.title;
		const file_title = data.file_title;
		const meta_title = title === file_title ? null : title;
		const hasThumbnail = data.with_thumbnails;
		const htmlID = `video-${data.video_id}`;
		const alreadyOpened = data.date != data.date_entry_opened;
		const common = (this.props.groupDef && this.props.groupDef.common) || {};
		const groupedBySimilarityID = this.props.groupDef && this.props.groupDef.field === "similarity_id";
		const errors = data.errors.slice();
		errors.sort();
		return (
			<div className={"video horizontal" + (data.found ? " found" : " not-found")}>
				<div className="image p-2">
					{hasThumbnail ? (
						<img alt={data.title} src={data.thumbnail_path} />
					) : (
						<div className="no-thumbnail">{tr("no thumbnail")}</div>
					)}
				</div>
				<div className="video-details horizontal flex-grow-1">
					{this.renderProperties()}
					<div className="info p-2">
						<div className="name">
							<div className="options horizontal">
								<MenuPack title={`${Characters.SETTINGS}`}>
								    {data.found ? (
								        <MenuItem action={this.markAsRead}>{tr("Mark as read")}</MenuItem>
								    ) : ("")}
									{data.found ? (
										<MenuItem action={this.openVideo}>{tr("Open file")}</MenuItem>
									) : (
										<div className="text-center">
											<strong>{tr("(not found)")}</strong>
										</div>
									)}
									{data.found && window.PYTHON_HAS_RUNTIME_VLC ? (
										<MenuItem action={this.openVideoSurely}>
											<strong>
												<em>{tr("Open file from local server")}</em>
											</strong>
										</MenuItem>
									) : (
										""
									)}
									{data.found ? (
										<MenuItem action={this.openContainingFolder}>
											{tr("Open containing folder")}
										</MenuItem>
									) : (
										""
									)}
									{meta_title ? (
										<MenuItem action={this.copyMetaTitle}>{tr("Copy meta title")}</MenuItem>
									) : (
										""
									)}
									{file_title ? (
										<MenuItem action={this.copyFileTitle}>{tr("Copy file title")}</MenuItem>
									) : (
										""
									)}
									<MenuItem action={this.copyFilePath}>{tr("Copy path")}</MenuItem>
									<MenuItem action={this.copyVideoID}>{tr("Copy video ID")}</MenuItem>
									{data.found ? (
										<MenuItem action={this.renameVideo}>{tr("Rename video")}</MenuItem>
									) : (
										""
									)}
									{data.found ? (
										<MenuItem action={this.moveVideo}>
											{tr("Move video to another folder ...")}
										</MenuItem>
									) : (
										""
									)}
									{this.props.groupedByMoves && data.moves.length ? (
										<Menu title="Confirm move to ...">
											{data.moves.map((dst, index) => (
												<MenuItem
													key={index}
													className="confirm-move"
													action={() => this.confirmMove(data.video_id, dst.video_id)}>
													<code>{dst.filename}</code>
												</MenuItem>
											))}
										</Menu>
									) : (
										""
									)}
									{groupedBySimilarityID ? (
										<MenuItem action={this.dismissSimilarity}>{tr("Dismiss similarity")}</MenuItem>
									) : (
										""
									)}
									{data.similarity_id !== null ? (
										<MenuItem action={this.resetSimilarity}>{tr("Reset similarity")}</MenuItem>
									) : (
										""
									)}
									{data.found ? (
									    <MenuItem className="red-brown" action={this.deleteVideoEntry}>
                                            {tr("Delete video entry")}
                                        </MenuItem>
									) : ""}
									<MenuItem className="red-flag" action={this.deleteVideo}>
										{data.found ? tr("Delete video") : tr("Delete entry")}
									</MenuItem>
								</MenuPack>
								<div title={data.video_id}>
									<input
										type="checkbox"
										checked={this.props.selected}
										id={htmlID}
										onChange={this.onSelect}
									/>
									&nbsp;
									<label htmlFor={htmlID}>
										<strong className="title">{data.title}</strong>
									</label>
								</div>
							</div>
							{data.title === data.file_title ? (
								""
							) : (
								<div className="file-title">
									<em>{data.file_title}</em>
								</div>
							)}
						</div>
						<div className={"filename-line" + (data.found ? "" : " horizontal")}>
							{data.found ? (
								""
							) : (
								<div className="prepend clickable" onClick={this.deleteVideo}>
									<code className="text-not-found">{tr("NOT FOUND")}</code>
									<code className="text-delete">{tr("DELETE")}</code>
								</div>
							)}
							<div className={`filename ${alreadyOpened ? "already-opened" : ""}`}>
								<code
									{...(data.found ? { className: "clickable" } : {})}
									{...(data.found ? { onClick: this.openVideo } : {})}>
									{data.filename}
								</code>
							</div>
						</div>
						<div className="format horizontal">
							<div className="prepend">
								<code className={cc(common.extension)}>{data.extension}</code>
							</div>
							<div>
								<strong title={data.file_size} className={cc(common.size)}>
									{data.size}
								</strong>{" "}
								/ <span className={cc(common.container_format)}>{data.container_format}</span> (
								<span title={data.video_codec_description} className={cc(common.video_codec)}>
									{data.video_codec}
								</span>
								,{" "}
								<span title={data.audio_codec_description} className={cc(common.audio_codec)}>
									{data.audio_codec}
								</span>
								)
							</div>
							<div className="prepend">
								<code>Bit rate</code>
							</div>
							<div className={cc(common.bit_rate)}>
								<strong>
									<em>{data.bit_rate}/s</em>
								</strong>
							</div>
						</div>
						<div>
							<strong className={cc(common.length)}>{data.length}</strong> |{" "}
							<strong className={cc(common.width)}>{data.width}</strong> x{" "}
							<strong className={cc(common.height)}>{data.height}</strong> @{" "}
							<span className={cc(common.frame_rate)}>
								{data.frame_rate} {tr("fps")}
							</span>
							,{" "}
							<span className={cc(common.bit_depth)}>
								{data.bit_depth} {tr("bits")}
							</span>{" "}
							|{" "}
							<span className={cc(common.sample_rate)}>
								{data.sample_rate} {tr("Hz")} x {data.audio_bits || "32?"} {tr("bits")} ({data.channels}{" "}
								{tr("channels")})
							</span>
							,{" "}
							<span title={data.audio_bit_rate} className={cc(common.audio_bit_rate)}>
								{audio_bit_rate} {tr("Kb/s")}
							</span>
						</div>
						<div>
							<code className={cc(common.date)}>{data.date}</code> |{" "}
							<em>
								(entry){" "}
								<code className={cc(common.date_entry_modified)}>{data.date_entry_modified}</code>
							</em>{" "}
							|{" "}
							<em>
								(opened) <code className={cc(common.date_entry_opened)}>{data.date_entry_opened}</code>
							</em>
						</div>
						<div>
							<strong>Audio</strong>:{" "}
							{data.audio_languages.length ? data.audio_languages.join(", ") : "(none)"} |{" "}
							<strong>Subtitles</strong>:{" "}
							{data.subtitle_languages.length ? data.subtitle_languages.join(", ") : "(none)"}
						</div>
						{errors.length ? (
							<div className="horizontal">
								<div>
									<strong>Errors:</strong>&nbsp;
								</div>
								<div>
									<div className="property">
										{errors.map((element, elementIndex) => (
											<span className="value" key={elementIndex}>
												{element.toString()}
											</span>
										))}
									</div>
								</div>
							</div>
						) : (
							""
						)}
						{!groupedBySimilarityID ? (
							<div>
								<strong>{tr("Similarity ID")}:</strong>{" "}
								<code>
									{data.similarity_id === null
										? tr("(not yet compared)")
										: data.similarity_id === -1
										? tr("(no similarities)")
										: data.similarity_id}
								</code>
							</div>
						) : (
							""
						)}
						{this.props.groupedByMoves && data.moves.length === 1 ? (
							<p>
								<button
									className="block"
									onClick={() => this.confirmMove(data.video_id, data.moves[0].video_id)}>
									<strong>{tr("Confirm move to")}:</strong>
									<br />
									<code>{data.moves[0].filename}</code>
								</button>
							</p>
						) : (
							""
						)}
					</div>
				</div>
			</div>
		);
	}

	renderVideoState() {
		const data = this.props.data;
		const errors = data.errors.slice();
		errors.sort();
		const alreadyOpened = APP_STATE.videoHistory.has(data.filename);
		return (
			<div className={"video horizontal" + (data.found ? " found" : " not-found")}>
				<div className="image p-2">
					<div className="no-thumbnail">{tr("no thumbnail")}</div>
				</div>
				<div className="video-details horizontal flex-grow-1">
					<div className="info p-2">
						<div className="name">
							<div className="options horizontal">
								<MenuPack title={`${Characters.SETTINGS}`}>
									{data.found ? (
										<MenuItem action={this.openVideo}>{tr("Open file")}</MenuItem>
									) : (
										<div className="text-center">
											<strong>{tr("(not found)")}</strong>
										</div>
									)}
									{data.found ? (
										<MenuItem action={this.openContainingFolder}>
											{tr("Open containing folder")}
										</MenuItem>
									) : (
										""
									)}
									<MenuItem action={this.copyFileTitle}>{tr("Copy file title")}</MenuItem>
									<MenuItem action={this.copyFilePath}>{tr("Copy path")}</MenuItem>
									{data.found ? (
										<MenuItem action={this.renameVideo}>{tr("Rename video")}</MenuItem>
									) : (
										""
									)}
									{data.found ? (
									    <MenuItem className="red-flag" action={this.deleteVideoEntry}>
                                            {tr("Delete video entry")}
                                        </MenuItem>
									) : ""}
									<MenuItem className="red-flag" action={this.deleteVideo}>
										{data.found ? tr("Delete video") : tr("Delete entry")}
									</MenuItem>
								</MenuPack>
								<div>
									<strong className="title">{data.file_title}</strong>
								</div>
							</div>
						</div>
						<div className={"filename-line" + (data.found ? "" : " horizontal")}>
							{data.found ? (
								""
							) : (
								<div className="prepend clickable" onClick={this.deleteVideo}>
									<code className="text-not-found">{tr("NOT FOUND")}</code>
									<code className="text-delete">{tr("DELETE")}</code>
								</div>
							)}
							<div className={`filename ${alreadyOpened ? "already-opened" : ""}`}>
								<code
									{...(data.found ? { className: "clickable" } : {})}
									{...(data.found ? { onClick: this.openVideo } : {})}>
									{data.filename}
								</code>
							</div>
						</div>
						<div className="format horizontal">
							<div className="prepend">
								<code>{data.extension}</code>
							</div>
							<div>
								<strong title={data.file_size}>{data.size}</strong>
							</div>
							{" | "}
							<div>
								<code>{data.date}</code>
							</div>
							<div>
								<em>
									(entry) <code>{data.date_entry_modified}</code>
								</em>{" "}
								|{" "}
								<em>
									(opened) <code>{data.date_entry_opened}</code>
								</em>
							</div>
						</div>
						<div className="horizontal">
							<div>
								<strong>{tr("Video unreadable")}:</strong>
							</div>
							<div>
								<div className="property">
									{errors.map((element, elementIndex) => (
										<span className="value" key={elementIndex}>
											{element.toString()}
										</span>
									))}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		);
	}

	renderProperties() {
		const props = this.props.data.properties;
		const propDefs = this.props.propDefs;
		if (!propDefs.length) return "";
		return (
			<div className="properties p-2">
				<div className="edit-properties clickable text-center mb-2" onClick={this.editProperties}>
					PROPERTIES
				</div>
				{propDefs.map((def) => {
					const name = def.name;
					const printableValues = props.hasOwnProperty(name) ? props[name] : def.defaultValues;
					const noValue =
						!printableValues.length || (printableValues.length === 1 && printableValues[0] === "");
					return noValue ? (
						""
					) : (
						<div key={name} className={`property ${props.hasOwnProperty(name) ? "defined" : ""}`}>
							<Collapsable title={name}>
								{printableValues.map((element, elementIndex) => (
									<span
										className="value clickable"
										key={elementIndex}
										onClick={() => this.props.onSelectPropertyValue(name, element)}>
										{element.toString()}
									</span>
								))}
							</Collapsable>
						</div>
					);
				})}
			</div>
		);
	}

	markAsRead() {
	    python_call("mark_as_read", this.props.data.video_id)
			.then(() => {
				APP_STATE.videoHistory.add(this.props.data.filename);
				this.props.onInfo(
					tr("Marked as read: {path}", {
						path: this.props.data.filename,
					}),
					true
				);
			})
			.catch((error) => {
				backend_error(error);
				this.props.onInfo(
					tr("Unable to mark as read: {path}", {
						path: this.props.data.filename,
					})
				);
			});
	}

	openVideo() {
		python_call("open_video", this.props.data.video_id)
			.then(() => {
				APP_STATE.videoHistory.add(this.props.data.filename);
				this.props.onInfo(
					tr("Opened: {path}", {
						path: this.props.data.filename,
					}),
					true
				);
			})
			.catch((error) => {
				backend_error(error);
				this.props.onInfo(
					tr("Unable to open: {path}", {
						path: this.props.data.filename,
					})
				);
			});
	}

	openVideoSurely() {
		python_call("open_from_server", this.props.data.video_id)
			.then((url) => {
				APP_STATE.videoHistory.add(this.props.data.filename);
				this.props.onInfo(tr("Opened: {path}", { path: url }), true);
			})
			.catch((error) => {
				backend_error(error);
				this.props.onInfo(
					tr("Unable to open: {path}", {
						path: this.props.data.filename,
					})
				);
			});
	}

	editProperties() {
		const data = this.props.data;
		Fancybox.load(
			<FormVideoEditProperties
				data={data}
				definitions={this.props.propDefs}
				onClose={(properties) => {
					python_call("set_video_properties", this.props.data.video_id, properties)
						.then(() =>
							this.props.onInfo(
								tr("Properties updated: {path}", {
									path: data.filename,
								}),
								true
							)
						)
						.catch(backend_error);
				}}
			/>
		);
	}

	confirmDeletion() {
		const filename = this.props.data.filename;
		const thumbnail_path = this.props.data.thumbnail_path;
		Fancybox.load(
			<Dialog title={tr("Confirm deletion")} yes={tr("DELETE")} action={this.reallyDeleteVideo}>
				<div className="form-delete-video text-center">
					{tr("## Are you sure you want to !!definitely!! delete this video?", null, "markdown")}
					<div className="details overflow-auto px-2 py-1">
						<code id="filename">{filename}</code>
					</div>
					<p>
						{this.props.data.with_thumbnails ? (
							<img id="thumbnail" alt="No thumbnail available" src={thumbnail_path} />
						) : (
							<div className="no-thumbnail">{tr("no thumbnail")}</div>
						)}
					</p>
				</div>
			</Dialog>
		);
	}

	deleteVideoEntry() {
		const filename = this.props.data.filename;
		const thumbnail_path = this.props.data.thumbnail_path;
		Fancybox.load(
			<Dialog title={tr("Confirm entry deletion")} yes={tr("DELETE ENTRY")} action={this.reallyDeleteVideoEntry}>
				<div className="form-delete-video text-center">
					{tr("## Are you sure you want to !!definitely!! delete **entry** for this video in database?", null, "markdown")}
					<div className="details overflow-auto px-2 py-1">
						<code id="filename">{filename}</code>
					</div>
					<p>
						{this.props.data.with_thumbnails ? (
							<img id="thumbnail" alt="No thumbnail available" src={thumbnail_path} />
						) : (
							<div className="no-thumbnail">{tr("no thumbnail")}</div>
						)}
					</p>
				</div>
			</Dialog>
		);
	}

	dismissSimilarity() {
		const filename = this.props.data.filename;
		const thumbnail_path = this.props.data.thumbnail_path;
		Fancybox.load(
			<Dialog title={tr("Dismiss similarity")} yes={tr("dismiss")} action={this.reallyDismissSimilarity}>
				<div className="form-delete-video text-center">
					<h2>{tr("Are you sure you want to dismiss similarity for this video?")}</h2>
					<div className="details overflow-auto px-2 py-1">
						<code id="filename">{filename}</code>
					</div>
					<p>
						{this.props.data.with_thumbnails ? (
							<img id="thumbnail" alt="No thumbnail available" src={thumbnail_path} />
						) : (
							<div className="no-thumbnail">{tr("no thumbnail")}</div>
						)}
					</p>
				</div>
			</Dialog>
		);
	}

	resetSimilarity() {
		const filename = this.props.data.filename;
		const thumbnail_path = this.props.data.thumbnail_path;
		Fancybox.load(
			<Dialog title={tr("Reset similarity")} yes={tr("reset")} action={this.reallyResetSimilarity}>
				<div className="form-delete-video text-center">
					{tr(
						`
## Are you sure you want to reset similarity for this video?

### Video will then be re-compared at next similarity search
`,
						null,
						"markdown"
					)}
					<div className="details overflow-auto px-2 py-1">
						<code id="filename">{filename}</code>
					</div>
					<p>
						{this.props.data.with_thumbnails ? (
							<img id="thumbnail" alt="No thumbnail available" src={thumbnail_path} />
						) : (
							<div className="no-thumbnail">{tr("no thumbnail")}</div>
						)}
					</p>
				</div>
			</Dialog>
		);
	}

	deleteVideo() {
		if (this.props.data.found || this.props.confirmDeletion) this.confirmDeletion();
		else this.reallyDeleteVideo();
	}

	reallyDeleteVideo() {
		python_call("delete_video", this.props.data.video_id)
			.then(() =>
				this.props.onInfo(
					tr("Video deleted! {path}", {
						path: this.props.data.filename,
					}),
					true
				)
			)
			.catch(backend_error);
	}

	reallyDeleteVideoEntry() {
		python_call("delete_video_entry", this.props.data.video_id)
			.then(() =>
				this.props.onInfo(
					tr("Video entry deleted! {path}", {
						path: this.props.data.filename,
					}),
					true
				)
			)
			.catch(backend_error);
	}

	reallyDismissSimilarity() {
		python_call("set_similarities", [this.props.data.video_id], [-1])
			.then(() =>
				this.props.onInfo(
					tr("Current similarity cancelled: {path}", {
						path: this.props.data.filename,
					}),
					true
				)
			)
			.catch(backend_error);
	}

	reallyResetSimilarity() {
		python_call("set_similarities", [this.props.data.video_id], [null])
			.then(() =>
				this.props.onInfo(
					tr("Current similarity reset: {path}", {
						path: this.props.data.filename,
					}),
					true
				)
			)
			.catch(backend_error);
	}

	openContainingFolder() {
		python_call("open_containing_folder", this.props.data.video_id)
			.then((folder) => {
				this.props.onInfo(tr("Opened folder: {path}", { path: folder }));
			})
			.catch(backend_error);
	}

	copyMetaTitle() {
		this.copyToClipboard("title");
	}

	copyFileTitle() {
		this.copyToClipboard("file_title");
	}

	copyFilePath() {
		this.copyToClipboard("filename");
	}

	copyVideoID() {
		this.copyToClipboard("video_id");
	}

	copyToClipboard(field) {
		const text = this.props.data[field];
		python_call("clipboard", text)
			.then(() => this.props.onInfo(tr("Copied to clipboard: {text}", { text })))
			.catch(() => this.props.onInfo(tr("Cannot copy {field} to clipboard: {text}", { field, text })));
	}

	confirmMove(srcID, dstID) {
		python_call("set_video_moved", srcID, dstID)
			.then(() =>
				this.props.onInfo(
					tr("Moved: {path}", {
						path: this.props.data.filename,
					}),
					true
				)
			)
			.catch(backend_error);
	}

	renameVideo() {
		const filename = this.props.data.filename;
		const title = this.props.data.file_title;
		Fancybox.load(
			<GenericFormRename
				title={tr("Rename video")}
				header={tr("Rename video")}
				description={filename}
				data={title}
				onClose={(newTitle) => {
					python_call("rename_video", this.props.data.video_id, newTitle)
						.then(() => this.props.onInfo(`Renamed: ${newTitle}`, true))
						.catch(backend_error);
				}}
			/>
		);
	}

	moveVideo() {
		python_call("select_directory", APP_STATE.latestMoveFolder)
			.then((directory) => {
				if (directory) {
					APP_STATE.latestMoveFolder = directory;
					this.props.onMove(this.props.data.video_id, directory);
				}
			})
			.catch(backend_error);
	}

	onSelect(event) {
		if (this.props.onSelect) {
			this.props.onSelect(this.props.data.video_id, event.target.checked);
		}
	}
}

Video.propTypes = {
	data: PropTypes.object.isRequired,
	propDefs: PropTypes.arrayOf(PropTypes.object).isRequired,
	groupDef: PropTypes.object.isRequired,
	confirmDeletion: PropTypes.bool,
	groupedByMoves: PropTypes.bool,
	selected: PropTypes.bool,
	// onSelect(videoID, selected)
	onSelect: PropTypes.func,
	// onSelectPropertyValue(propName, propVal)
	onSelectPropertyValue: PropTypes.func.isRequired,
	// onInfo(message: str, backendUpdated: bool)
	onInfo: PropTypes.func.isRequired,
	// onMove(videoID, directory)
	onMove: PropTypes.func.isRequired,
};
