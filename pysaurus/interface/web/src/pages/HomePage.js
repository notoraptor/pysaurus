import {Characters} from "../utils/constants.js";
import {backend_error, python_call} from "../utils/backend.js";
import {formatString} from "../utils/functions.js";

class ProgressionMonitoring {
    constructor(name, total) {
        this.name = name;
        this.total = total;
        this.title = null;
        this.jobs = new Map();
    }

    collectJobStep(notification) {
        this.jobs.set(notification.notification.channel, notification.notification.step);
        this.title = notification.notification.title;
    }
}

/**
 * @param props {{monitoring: ProgressionMonitoring}}
 */
function Monitoring(props) {
    const monitoring = props.monitoring;
    const total = monitoring.total;
    let current = 0;
    for (let step of monitoring.jobs.values()) {
        current += step;
    }
    const percent = Math.round(current * 100 / total);
    const title = monitoring.title || formatString(PYTHON_LANG.text_done, {count: current});
    const jobClassID = "job " + monitoring.name;
    return (
        <div className="job horizontal">
            <label htmlFor={jobClassID} className="pr-2">{title} ({percent} %)</label>
            <progress className="flex-grow-1" id={jobClassID} value={current} max={total}/>
        </div>
    );
}

const EndStatus = {
    DatabaseReady: null,
    Done: "Done!",
    Cancelled: "Cancelled.",
    End: "Ended.",
}
const EndReady = {
    DatabaseReady: true,
    Done: true,
    Cancelled: true,
    End: false,
}

function collectEndNotification(app, notification) {
    const name = notification.name;
    app.collectNotification(notification, {loaded: name, status: EndStatus[name], ready: EndReady[name]});
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
        app.collectNotification(notification, {jobMap});
    },
    JobStep: function (app, notification) {
        const lastIndex = app.state.messages.length - 1;
        const jobsAreAlreadyCollected = app.state.jobMap.get(notification.notification.name).jobs.size;
        const jobMap = new Map(app.state.jobMap);
        jobMap.get(notification.notification.name).collectJobStep(notification);
        app.collectNotification(notification, {jobMap}, !jobsAreAlreadyCollected);
    },
    ProfilingEnd: function (app, notification) {
        const messages = app.state.messages.slice();
        const lastIndex = messages.length - 1;
        if (
            messages.length
            && messages[lastIndex].name === "ProfilingStart"
            && messages[lastIndex].notification.name === notification.notification.name
        ) {
            messages.pop();
            notification.notification.inplace = true;
        }
        messages.push(notification);
        app.setState({messages});
    }
};

const NotificationRenderer = {
    JobStep: (app, message, i) => <Monitoring monitoring={app.state.jobMap.get(message.notification.name)} key={i}/>,
    DatabaseLoaded: function (app, message, i) {
        const data = message.notification;
        return (
            <div key={i}>
                <strong>{message.name === 'DatabaseSaved' ? PYTHON_LANG.text_database_saved : PYTHON_LANG.text_database_loaded}</strong>:
                {formatString(PYTHON_LANG.text_nb_entries, {count: data.entries}) + ", "}
                {formatString(PYTHON_LANG.text_nb_discarded, {count: data.discarded}) + ", "}
                {formatString(PYTHON_LANG.text_nb_unreadable_not_found, {count: data.unreadable_not_found}) + ", "}
                {formatString(PYTHON_LANG.text_nb_unreadable_found, {count: data.unreadable_found}) + ", "}
                {formatString(PYTHON_LANG.text_nb_readable_not_found, {count: data.readable_not_found}) + ", "}
                {formatString(PYTHON_LANG.text_nb_readable_found_without_thumbnails, {count: data.readable_found_without_thumbnails}) + ", "}
                {formatString(PYTHON_LANG.text_nb_valid, {count: data.valid})}
            </div>
        );
    },
    DatabaseSaved: function (app, message, i) {
        return NotificationRenderer.DatabaseLoaded(app, message, i);
    },
    DatabaseReady: function (app, message, i) {
        return <div key={i}><strong>{PYTHON_LANG.text_notification_database_ready}</strong></div>;
    },
    Done: function (app, message, i) {
        return <div key={i}><strong>{PYTHON_LANG.text_notification_done}</strong></div>;
    },
    Cancelled: function (app, message, i) {
        return <div key={i}><strong>{PYTHON_LANG.text_notification_cancelled}</strong></div>;
    },
    End: function (app, message, i) {
        const info = message.notification.message;
        return <div key={i}><strong>Ended.{info ? ` ${info}` : ""}</strong></div>;
    },
    FinishedCollectingVideos: function (app, message, i) {
        const count = message.notification.count;
        return (<div key={i}>{markdownToReact(formatString(PYTHON_LANG.gui_home_collected_files, {count}), true)}</div>);
    },
    MissingThumbnails: function (app, message, i) {
        const names = message.notification.names;
        if (names.length) {
            return (
                <div key={i}>
                    <div><strong>{formatString(PYTHON_LANG.text_notification_missing_thumbnails, {count: names.length})}</strong>:</div>
                    {names.map((name, indexName) => <div key={indexName}><code>{name}</code></div>)}
                </div>
            );
        } else {
            return (<div key={i}><em>{PYTHON_LANG.text_notification_no_missing_thumbnails}</em></div>);
        }
    },
    ProfilingStart: function (app, message, i) {
        return (
            <div key={i}><span className="span-profiled">{PYTHON_LANG.text_profiling}</span> {message.notification.name}</div>
        );
    },
    ProfilingEnd: function (app, message, i) {
        return (
            <div key={i}>
                <span className="span-profiled">{message.notification.inplace ? `${PYTHON_LANG.text_profiling} / ` : ""}{PYTHON_LANG.text_profiled}</span>{" "}
                {message.notification.name}{" "}
                <span className="span-profiled">TIME</span>{" "}
                {message.notification.time}
            </div>
        );
    },
    VideoInfoErrors: function (app, message, i) {
        const errors = message.notification.video_errors;
        const keys = Object.keys(errors);
        keys.sort();
        return (
            <div key={i}>
                <div>
                    <strong>
                        {formatString(
                            (message.name === 'VideoInfoErrors' ? PYTHON_LANG.text_nb_video_errors : PYTHON_LANG.text_nb_thumbnail_errors),
                            {count: keys.length}
                        )}
                    </strong>:
                </div>
                <ul>{keys.map((name, indexName) => (
                    <li key={indexName}>
                        <div><code>{name}</code></div>
                        <ul>{errors[name].map((error, indexError) => (
                            <li key={indexError}><code>{error}</code></li>
                        ))}</ul>
                    </li>
                ))}</ul>
            </div>
        );
    },
    VideoThumbnailErrors: function (app, message, i) {
        return NotificationRenderer.VideoInfoErrors(app, message, i);
    },
    JobToDo: function (app, message, i) {
        const total = message.notification.total;
        const label = message.notification.name;
        const title = message.notification.title;
        if (title) {
            return <div key={i}><strong>{title}</strong></div>;
        } else if (total) {
            return (<div key={i}>{PYTHON_LANG.gui_home_to_load}: <strong>{total}{" "}{label}</strong></div>);
        } else {
            return (<div key={i}><em>{PYTHON_LANG.gui_home_to_load}: {PYTHON_LANG.text_nothing}</em></div>);
        }
    },
    NbMiniatures: function (app, message, i) {
        const total = message.notification.total;
        if (total) {
            return (<div key={i}><strong>{formatString(PYTHON_LANG.text_nb_miniatures_saved, {count: total})}</strong></div>);
        } else {
            return (<div key={i}><em>{PYTHON_LANG.text_no_miniatures_saved}</em></div>);
        }
    },
    Message: function (app, message, i) {
        return <div key={i}><strong>{Characters.WARNING_SIGN}</strong> {message.notification.message}</div>;
    }
};

const ACTIONS = {
    update_database: "Update database",
    find_similar_videos: "Find similarities",
    find_similar_videos_ignore_cache: "Find similarities (ignore cache)",
    create_database: "Create database",
    open_database: "Open database",
    move_video_file: "Move video file",
    compute_predictor: "Compute predictor",
    apply_predictor: "Predict"
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
                <div id="notifications" className="notifications flex-grow-1 overflow-auto">
                    {this.renderMessages()}
                </div>
            </div>
        );
    }

    renderInitialButton() {
        if (this.props.parameters.onReady)
            return <strong>{this.state.status || (ACTIONS[this.props.parameters.command[0]] + " ...")}</strong>;
        else if (this.state.loaded)
            return <button onClick={this.displayVideos}>{PYTHON_LANG.text_display_videos}</button>;
        else
            return <button disabled={true}>{ACTIONS[this.props.parameters.command[0]]} ...</button>;
    }

    renderMessages() {
        const output = [];
        for (let i = 0; i < this.state.messages.length; ++i) {
            const message = this.state.messages[i];
            const name = message.name;
            if (NotificationRenderer[name]) {
                const display = NotificationRenderer[name](this, message, i);
                if (display)
                    output.push(display);
            } else {
                output.push(<div key={i}><em>{PYTHON_LANG.text_notification_unknown}</em>: {message.message}</div>);
            }
        }
        if (!this.state.loaded)
            output.push(<div key={this.state.messages.length}>...</div>);
        return output;
    }

    componentDidMount() {
        this.callbackIndex = NOTIFICATION_MANAGER.register(this.notify);
        python_call(...this.props.parameters.command)
            .catch(backend_error);
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
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
        else
            this.collectNotification(notification);
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

HomePage.propTypes = {
    app: PropTypes.object.isRequired,
    parameters: PropTypes.shape({
        command: PropTypes.array.isRequired,
        // onReady(notificationName)
        onReady: PropTypes.func
    })
};