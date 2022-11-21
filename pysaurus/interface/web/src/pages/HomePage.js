import { Characters } from "../utils/constants.js";
import { backend_error, python_call } from "../utils/backend.js";
import { LangContext } from "../language.js";

class ProgressionMonitoring {
	constructor(name, total) {
		this.name = name;
		this.total = total;
		this.title = null;
		this.jobs = new Map();
	}

	collectJobStep(notification) {
		this.jobs.set(
			notification.notification.channel,
			notification.notification.step
		);
		this.title = notification.notification.title;
	}
}

class Monitoring extends React.Component {
	render() {
		const monitoring = this.props.monitoring;
		const total = monitoring.total;
		let current = 0;
		for (let step of monitoring.jobs.values()) {
			current += step;
		}
		const percent = Math.round((current * 100) / total);
		const title = monitoring.title || tr("{count} done", { count: current });
		const jobClassID = "job " + monitoring.name;
		return (
			<div className="job horizontal">
				<label htmlFor={jobClassID} className="pr-2">
					{title} ({percent} %)
				</label>
				<progress
					className="flex-grow-1"
					id={jobClassID}
					value={current}
					max={total}
				/>
			</div>
		);
	}
}
Monitoring.contextType = LangContext;
Monitoring.propTypes = {
	monitoring: PropTypes.instanceOf(ProgressionMonitoring).isRequired,
};

const EndStatus = {
	DatabaseReady: null,
	Done: "Done!",
	Cancelled: "Cancelled.",
	End: "Ended.",
};
const EndReady = {
	DatabaseReady: true,
	Done: true,
	Cancelled: true,
	End: false,
};

function collectEndNotification(app, notification) {
	const name = notification.name;
	app.collectNotification(notification, {
		loaded: name,
		status: EndStatus[name],
		ready: EndReady[name],
	});
}

const NotificationCollector = {
	DatabaseReady: collectEndNotification,
	Done: collectEndNotification,
	Cancelled: collectEndNotification,
	End: collectEndNotification,
	JobToDo: function (app, notification) {
		const name = notification.notification.name;
		const total = notification.notification.total;
		const jobMap = new Map(app.state.jobMap);
		jobMap.set(name, new ProgressionMonitoring(name, total));
		app.collectNotification(notification, { jobMap });
	},
	JobStep: function (app, notification) {
		const jobsAreAlreadyCollected = app.state.jobMap.get(
			notification.notification.name
		).jobs.size;
		const jobMap = new Map(app.state.jobMap);
		jobMap.get(notification.notification.name).collectJobStep(notification);
		app.collectNotification(notification, { jobMap }, !jobsAreAlreadyCollected);
	},
	ProfilingEnd: function (app, notification) {
		const messages = app.state.messages.slice();
		const lastIndex = messages.length - 1;
		if (
			messages.length &&
			messages[lastIndex].name === "ProfilingStart" &&
			messages[lastIndex].notification.name === notification.notification.name
		) {
			messages.pop();
			notification.notification.inplace = true;
		}
		messages.push(notification);
		app.setState({ messages });
	},
};

class NotificationRenderer extends React.Component {
	constructor(props) {
		// {app: HomePage object, message: Notification from Python, i: int}
		super(props);
		this.JobStep = this.JobStep.bind(this);
		this.DatabaseLoaded = this.DatabaseLoaded.bind(this);
		this.DatabaseSaved = this.DatabaseSaved.bind(this);
		this.DatabaseReady = this.DatabaseReady.bind(this);
		this.Done = this.Done.bind(this);
		this.Cancelled = this.Cancelled.bind(this);
		this.End = this.End.bind(this);
		this.FinishedCollectingVideos = this.FinishedCollectingVideos.bind(this);
		this.MissingThumbnails = this.MissingThumbnails.bind(this);
		this.ProfilingStart = this.ProfilingStart.bind(this);
		this.ProfilingEnd = this.ProfilingEnd.bind(this);
		this.VideoInfoErrors = this.VideoInfoErrors.bind(this);
		this.VideoThumbnailErrors = this.VideoThumbnailErrors.bind(this);
		this.JobToDo = this.JobToDo.bind(this);
		this.NbMiniatures = this.NbMiniatures.bind(this);
		this.Message = this.Message.bind(this);
	}
	render() {
		const app = this.props.app;
		const message = this.props.message;
		const i = this.props.i;
		const name = message.name;
		if (this.hasOwnProperty(name)) {
			return this[name](app, message, i);
		} else {
			return (
				<div key={i}>
					<em>{tr("unknown")}</em>: {message.message}
				</div>
			);
		}
	}
	JobStep(app, message, i) {
		return (
			<Monitoring
				monitoring={app.state.jobMap.get(message.notification.name)}
				key={i}
			/>
		);
	}
	DatabaseLoaded(app, message, i) {
		const data = message.notification;
		return (
			<div key={i}>
				<strong>
					{message.name === "DatabaseSaved"
						? tr("Database saved")
						: tr("Database loaded")}
				</strong>
				:{tr("{count} entries", { count: data.entries }) + ", "}
				{tr("{count} discarded", {
					count: data.discarded,
				}) + ", "}
				{tr("{count} unreadable not found", {
					count: data.unreadable_not_found,
				}) + ", "}
				{tr("{count} unreadable found", {
					count: data.unreadable_found,
				}) + ", "}
				{tr("{count} readable not found", {
					count: data.readable_not_found,
				}) + ", "}
				{tr("{count} readable found without thumbnails", {
					count: data.readable_found_without_thumbnails,
				}) + ", "}
				{tr("{count} valid", { count: data.valid })}
			</div>
		);
	}
	DatabaseSaved(app, message, i) {
		return this.DatabaseLoaded(app, message, i);
	}
	DatabaseReady(app, message, i) {
		return (
			<div key={i}>
				<strong>{tr("Database open!")}</strong>
			</div>
		);
	}
	Done(app, message, i) {
		return (
			<div key={i}>
				<strong>{tr("Done!")}</strong>
			</div>
		);
	}
	Cancelled(app, message, i) {
		return (
			<div key={i}>
				<strong>{tr("Cancelled.")}</strong>
			</div>
		);
	}
	End(app, message, i) {
		const info = message.notification.message;
		return (
			<div key={i}>
				<strong>Ended.{info ? ` ${info}` : ""}</strong>
			</div>
		);
	}
	FinishedCollectingVideos(app, message, i) {
		const count = message.notification.count;
		return (
			<div key={i}>
				{tr("**Collected** {count} file(s)", { count }).markdown(true)}
			</div>
		);
	}
	MissingThumbnails(app, message, i) {
		const names = message.notification.names;
		if (names.length) {
			return (
				<div key={i}>
					<div>
						<strong>
							{tr("Missing {count} thumbnails", {
								count: names.length,
							})}
						</strong>
						:
					</div>
					{names.map((name, indexName) => (
						<div key={indexName}>
							<code>{name}</code>
						</div>
					))}
				</div>
			);
		} else {
			return (
				<div key={i}>
					<em>{tr("No missing thumbnails!")}</em>
				</div>
			);
		}
	}
	ProfilingStart(app, message, i) {
		return (
			<div key={i}>
				<span className="span-profiled">{tr("PROFILING")}</span>{" "}
				{message.notification.name}
			</div>
		);
	}
	ProfilingEnd(app, message, i) {
		return (
			<div key={i}>
				<span className="span-profiled">
					{message.notification.inplace ? `${tr("PROFILING")} / ` : ""}
					{tr("PROFILED")}
				</span>{" "}
				{message.notification.name} <span className="span-profiled">TIME</span>{" "}
				{message.notification.time}
			</div>
		);
	}
	VideoInfoErrors(app, message, i) {
		const errors = message.notification.video_errors;
		const keys = Object.keys(errors);
		keys.sort();
		return (
			<div key={i}>
				<div>
					<strong>
						{tr(
							message.name === "VideoInfoErrors"
								? "{count} video error(s)"
								: "{count} thumbnail error(s)",
							{ count: keys.length }
						)}
					</strong>
					:
				</div>
				<ul>
					{keys.map((name, indexName) => (
						<li key={indexName}>
							<div>
								<code>{name}</code>
							</div>
							<ul>
								{errors[name].map((error, indexError) => (
									<li key={indexError}>
										<code>{error}</code>
									</li>
								))}
							</ul>
						</li>
					))}
				</ul>
			</div>
		);
	}
	VideoThumbnailErrors(app, message, i) {
		return this.VideoInfoErrors(app, message, i);
	}
	JobToDo(app, message, i) {
		const total = message.notification.total;
		const label = message.notification.name;
		const title = message.notification.title;
		if (title) {
			return (
				<div key={i}>
					<strong>{title}</strong>
				</div>
			);
		} else if (total) {
			return (
				<div key={i}>
					{tr("To load")}:{" "}
					<strong>
						{total} {label}
					</strong>
				</div>
			);
		} else {
			return (
				<div key={i}>
					<em>
						{tr("To load")}: {tr("nothing!")}
					</em>
				</div>
			);
		}
	}
	NbMiniatures(app, message, i) {
		const total = message.notification.total;
		if (total) {
			return (
				<div key={i}>
					<strong>
						{tr("{count} miniature(s) saved.", {
							count: total,
						})}
					</strong>
				</div>
			);
		} else {
			return (
				<div key={i}>
					<em>{tr("No miniatures saved!")}</em>
				</div>
			);
		}
	}
	Message(app, message, i) {
		return (
			<div key={i}>
				<strong>{Characters.WARNING_SIGN}</strong>{" "}
				{message.notification.message}
			</div>
		);
	}
}
NotificationRenderer.contextType = LangContext;

const ACTIONS = {
	update_database: "Update database",
	find_similar_videos: "Find similarities",
	find_similar_videos_ignore_cache: "Find similarities (ignore cache)",
	create_database: "Create database",
	open_database: "Open database",
	move_video_file: "Move video file",
	compute_predictor: "Compute predictor",
	apply_predictor: "Predict",
};

export class HomePage extends React.Component {
	constructor(props) {
		// parameters: {command: [name, ...args]}
		// app: App
		super(props);
		this.state = {
			loaded: false,
			ready: false,
			status: null,
			messages: [],
			jobMap: new Map(),
		};
		this.callbackIndex = -1;
		this.notify = this.notify.bind(this);
		this.displayVideos = this.displayVideos.bind(this);
		this.collectNotification = this.collectNotification.bind(this);
	}

	render() {
		return (
			<div id="home" className="absolute-plain p-4 vertical">
				<div className="text-center p-2">{this.renderInitialButton()}</div>
				<div
					id="notifications"
					className="notifications flex-grow-1 overflow-auto">
					{this.renderMessages()}
				</div>
			</div>
		);
	}

	renderInitialButton() {
		if (this.props.parameters.onReady)
			return (
				<strong>
					{this.state.status ||
						ACTIONS[this.props.parameters.command[0]] + " ..."}
				</strong>
			);
		else if (this.state.loaded)
			return <button onClick={this.displayVideos}>{tr("Display videos")}</button>;
		else
			return (
				<button disabled={true}>
					{ACTIONS[this.props.parameters.command[0]]} ...
				</button>
			);
	}

	renderMessages() {
		const output = this.state.messages.map((message, i) => (
			<NotificationRenderer app={this} message={message} i={i} />
		));
		if (!this.state.loaded)
			output.push(<div key={this.state.messages.length}>...</div>);
		return output;
	}

	componentDidMount() {
		this.callbackIndex = NOTIFICATION_MANAGER.register(this.notify);
		python_call(...this.props.parameters.command).catch(backend_error);
	}

	componentDidUpdate() {
		const divNotifs = document.getElementById("notifications");
		divNotifs.scrollTop = divNotifs.scrollHeight;
		if (this.props.parameters.onReady && this.state.ready) {
			setTimeout(() => this.props.parameters.onReady(this.state.loaded), 500);
		}
	}

	componentWillUnmount() {
		NOTIFICATION_MANAGER.unregister(this.callbackIndex);
	}

	notify(notification) {
		const name = notification.name;
		if (NotificationCollector[name])
			return NotificationCollector[name](this, notification);
		else this.collectNotification(notification);
	}

	displayVideos() {
		this.props.app.loadVideosPage();
	}

	/**
	 * Callback to collect notification.
	 * Update component with given updates,
	 * and register notification object if `store` parameter is true.
	 * @param notification {Object} - Notification to store
	 * @param updates {Object} - Object to update component
	 * @param store {boolean} - If true, append notification to internal notification list.
	 */
	collectNotification(notification, updates = {}, store = true) {
		if (store) {
			const messages = this.state.messages.slice();
			messages.push(notification);
			updates.messages = messages;
		}
		this.setState(updates);
	}
}
HomePage.contextType = LangContext;
HomePage.propTypes = {
	app: PropTypes.object.isRequired,
	parameters: PropTypes.shape({
		command: PropTypes.array.isRequired,
		// onReady(notificationName)
		onReady: PropTypes.func,
	}),
};
