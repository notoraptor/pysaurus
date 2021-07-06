import {HomeStatus} from "../utils/constants.js";
import {backend_error, python_call} from "../utils/backend.js";

class ProgressionMonitoring {
    constructor(name, total) {
        this.name = name;
        this.total = total;
        this.jobs = new Map();
    }

    collectJobStep(notification) {
        this.jobs.set(notification.notification.channel, notification.notification.step);
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
    const jobClassID = monitoring.name + "-job";
    return (
        <div className={`job horizontal ${jobClassID}`}>
            <label htmlFor={jobClassID} className="info">{current} / {total} ({percent} %)</label>
            <progress id={jobClassID} value={current} max={total}/>
        </div>
    );
}

const NotificationCollector = {
    DatabaseReady: function (app, notification) {
        app.collectNotification(
            notification,
            {status: HomeStatus.LOADED});
    },
    JobToDo: function (app, notification) {
        const name = notification.notification.name;
        const total = notification.notification.total;
        const jobMap = new Map(app.state.jobMap);
        jobMap.set(name, new ProgressionMonitoring(name, total));
        app.collectNotification(notification, {jobMap});
    },
    JobStep: function (app, notification) {
        const lastIndex = app.state.messages.length - 1;
        const jobIsBeingCollected = (
            lastIndex > -1
            && app.state.messages[lastIndex].name === notification.name
            && app.state.messages[lastIndex].notification.name === notification.notification.name
        );
        const jobMap = new Map(app.state.jobMap);
        jobMap.get(notification.notification.name).collectJobStep(notification);
        app.collectNotification(notification, {jobMap}, !jobIsBeingCollected);
    },
    // notifications ignored.
    ProfilingStart: function (app, notification) {}
};

const NotificationRenderer = {
    JobStep: (app, message, i) => <Monitoring monitoring={app.state.jobMap.get(message.notification.name)} key={i}/>,
    DatabaseLoaded: function (app, message, i) {
        const data = message.notification;
        return (
            <div key={i}>
                <strong>Database {message.name === 'DatabaseSaved' ? 'saved' : 'loaded'}</strong>:
                {data.entries}{' '}{data.entries > 1 ? 'entries' : 'entry'},
                {data.discarded} discarded,
                {data.unreadable_not_found} unreadable not found,
                {data.unreadable_found} unreadable found,
                {data.readable_not_found} readable not found,
                {data.readable_found_without_thumbnails} readable found without thumbnails,
                {data.valid} valid
            </div>
        );
    },
    DatabaseSaved: function (app, message, i) {
        return NotificationRenderer.DatabaseLoaded(app, message, i);
    },
    DatabaseReady: function (app, message, i) {
        return <div key={i}><strong>Database open!</strong></div>;
    },
    FinishedCollectingVideos: function (app, message, i) {
        const count = message.notification.count;
        return (<div key={i}><strong>Collected</strong>{' '}{count} file{count > 1 ? 's' : ''}</div>);
    },
    MissingThumbnails: function (app, message, i) {
        const names = message.notification.names;
        if (names.length) {
            return (
                <div key={i}>
                    <div><strong>Missing {names.length} thumbnails</strong>:</div>
                    {names.map((name, indexName) => <div key={indexName}><code>{name}</code></div>)}
                </div>
            );
        } else {
            return (<div key={i}><em>No missing thumbnails!</em></div>);
        }
    },
    ProfilingEnd: function (app, message, i) {
        // return (<div key={i}><strong>Loaded</strong> in {message.notification.time}</div>);
    },
    VideoInfoErrors: function (app, message, i) {
        const errors = message.notification.video_errors;
        const keys = Object.keys(errors);
        keys.sort();
        return (
            <div key={i}>
                <div>
                    <strong>
                        {errors.length}{' '}{message.name === 'VideoInfoErrors' ? 'video' : 'thumbnail'}{" "}
                        error{errors.length > 1 ? 's' : ''}
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
        if (total) {
            return (<div key={i}><strong>{total}{' '}{label}{total > 1 ? 's' : ''} to load.</strong></div>);
        } else {
            return (<div key={i}><em>No {label}s to load!</em></div>);
        }
    },
    NbMiniatures: function (app, message, i) {
        const total = message.notification.total;
        if (total) {
            return (<div key={i}><strong>{total} miniature{total > 1 ? 's' : ''} saved.</strong></div>);
        } else {
            return (<div key={i}><em>No miniatures saved!</em></div>);
        }
    },
};

export class HomePage extends React.Component {
    constructor(props) {
        // parameters: {update: bool = false}
        // app: App
        super(props);
        this.state = {
            status: this.props.parameters.update ? HomeStatus.LOADING : HomeStatus.INITIAL,
            messages: [],
            jobMap: new Map(),
            update: false,
        };
        this.callbackIndex = -1;
        this.notify = this.notify.bind(this);
        this.loadDatabase = this.loadDatabase.bind(this);
        this.displayVideos = this.displayVideos.bind(this);
        this.onChangeUpdate = this.onChangeUpdate.bind(this);
        this.collectNotification = this.collectNotification.bind(this);
    }

    render() {
        return (
            <div id="home">
                <div className="buttons">
                    {this.state.status === HomeStatus.INITIAL ? (
                        <span className="input-update">
                            <input type="checkbox"
                                   id="update"
                                   checked={this.state.update}
                                   onChange={this.onChangeUpdate}/>
                            {' '}
                            <label htmlFor="update">Update on load</label>
                        </span>
                    ) : ''}
                    {this.renderInitialButton()}
                </div>
                <div className="notifications">{this.renderMessages()}</div>
            </div>
        );
    }

    renderInitialButton() {
        const status = this.state.status;
        const update = this.props.parameters.update;
        if (status === HomeStatus.INITIAL)
            return <button onClick={this.loadDatabase}>Load database</button>;
        if (status === HomeStatus.LOADING)
            return <button disabled={true}>{update ? 'Updating' : 'Loading'} database ...</button>;
        if (status === HomeStatus.LOADED)
            return <button onClick={this.displayVideos}>Display videos</button>;
    }

    renderMessages() {
        const output = [];
        const lastIndex = this.state.messages.length - 1;
        for (let i = 0; i < this.state.messages.length; ++i) {
            const message = this.state.messages[i];
            const name = message.name;
            if (NotificationRenderer[name]) {
                const display = NotificationRenderer[name](this, message, i);
                if (display)
                    output.push(display);
            } else {
                output.push(<div key={i}><em>unknown</em>: {message.message}</div>);
            }
        }
        const ready = lastIndex > -1 && this.state.messages[lastIndex].name === "DatabaseReady";
        if (!ready && this.status === HomeStatus.LOADING)
            output.push(<div key={this.state.messages.length}>...</div>);
        return output;
    }

    componentDidMount() {
        this.callbackIndex = NOTIFICATION_MANAGER.register(this.notify);
        if (this.props.parameters.update)
            python_call('update_database');
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

    loadDatabase() {
        python_call('load_database', this.state.update)
            .then(() => {
                this.setState({status: HomeStatus.LOADING});
            })
            .catch(backend_error);
    }

    displayVideos() {
        this.props.app.loadVideosPage();
    }

    onChangeUpdate(event) {
        this.setState({update: event.target.checked});
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
