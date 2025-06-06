System.register(["../BaseComponent.js", "../language.js", "../utils/backend.js", "../utils/constants.js"], function (_export, _context) {
  "use strict";

  var BaseComponent, tr, backend_error, python_call, Characters, ProgressionMonitoring, Monitoring, NotificationRenderer, HomePage, EndStatus, EndReady, ACTIONS;
  _export("HomePage", void 0);
  return {
    setters: [function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }, function (_languageJs) {
      tr = _languageJs.tr;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
    }],
    execute: function () {
      ProgressionMonitoring = class ProgressionMonitoring {
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
      };
      Monitoring = class Monitoring extends React.Component {
        render() {
          const monitoring = this.props.monitoring;
          const total = monitoring.total;
          let current = 0;
          for (let step of monitoring.jobs.values()) {
            current += step;
          }
          const percent = Math.round(current * 100 / total);
          const title = monitoring.title || tr("{count} done", {
            count: current
          });
          const jobClassID = "job " + monitoring.name;
          return /*#__PURE__*/React.createElement("div", {
            className: "job horizontal"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: jobClassID,
            className: "pr-2"
          }, title, " (", percent, " %)"), /*#__PURE__*/React.createElement("progress", {
            className: "flex-grow-1",
            id: jobClassID,
            value: current,
            max: total
          }));
        }
      };
      Monitoring.propTypes = {
        monitoring: PropTypes.instanceOf(ProgressionMonitoring).isRequired
      };
      EndStatus = {
        DatabaseReady: null,
        Done: "Done!",
        Cancelled: "Cancelled.",
        End: "Ended."
      };
      EndReady = {
        DatabaseReady: true,
        Done: true,
        Cancelled: true,
        End: false
      };
      NotificationRenderer = class NotificationRenderer extends BaseComponent {
        // {app: HomePage object, message: Notification from Python, i: int}

        render() {
          const app = this.props.app;
          const message = this.props.message;
          const i = this.props.i;
          const name = message.name;
          if (this.hasOwnProperty(name)) {
            return this[name](app, message, i);
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, tr("unknown")), ": ", message.message);
          }
        }
        JobStep(app, message, i) {
          return /*#__PURE__*/React.createElement(Monitoring, {
            monitoring: app.state.jobMap.get(message.notification.name),
            key: i
          });
        }
        DatabaseLoaded(app, message, i) {
          const data = message.notification;
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, message.name === "DatabaseSaved" ? tr("Database saved") : tr("Database loaded")), ":", tr("{count} entries", {
            count: data.entries
          }) + ", ", tr("{count} discarded", {
            count: data.discarded
          }) + ", ", tr("{count} unreadable not found", {
            count: data.unreadable_not_found
          }) + ", ", tr("{count} unreadable found", {
            count: data.unreadable_found
          }) + ", ", tr("{count} readable not found", {
            count: data.readable_not_found
          }) + ", ", tr("{count} readable found without thumbnails", {
            count: data.readable_found_without_thumbnails
          }) + ", ", tr("{count} valid", {
            count: data.valid
          }));
        }
        DatabaseSaved(app, message, i) {
          return this.DatabaseLoaded(app, message, i);
        }
        DatabaseReady(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, tr("Database open!")));
        }
        Done(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, tr("Done!")));
        }
        Cancelled(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, tr("Cancelled.")));
        }
        End(app, message, i) {
          const info = message.notification.message;
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Ended.", info ? ` ${info}` : ""));
        }
        FinishedCollectingVideos(app, message, i) {
          const count = message.notification.count;
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, tr("**Collected** {count} file(s)", {
            count
          }, "markdown-inline"));
        }
        MissingThumbnails(app, message, i) {
          const names = message.notification.names;
          if (names.length) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, tr("Missing {count} thumbnails", {
              count: names.length
            })), ":"), names.map((name, indexName) => /*#__PURE__*/React.createElement("div", {
              key: indexName
            }, /*#__PURE__*/React.createElement("code", null, name))));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, tr("No missing thumbnails!")));
          }
        }
        ProfilingStart(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, tr("PROFILING")), " ", message.notification.name);
        }
        ProfilingEnd(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, message.notification.inplace ? `${tr("PROFILING")} / ` : "", tr("PROFILED")), " ", message.notification.name, " ", /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, "TIME"), " ", message.notification.time);
        }
        VideoInfoErrors(app, message, i) {
          const errors = message.notification.video_errors;
          const keys = Object.keys(errors);
          keys.sort();
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, tr(message.name === "VideoInfoErrors" ? "{count} video error(s)" : "{count} thumbnail error(s)", {
            count: keys.length
          })), ":"), /*#__PURE__*/React.createElement("ul", null, keys.map((name, indexName) => /*#__PURE__*/React.createElement("li", {
            key: indexName
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("code", null, name)), /*#__PURE__*/React.createElement("ul", null, errors[name].map((error, indexError) => /*#__PURE__*/React.createElement("li", {
            key: indexError
          }, /*#__PURE__*/React.createElement("code", null, error))))))));
        }
        VideoThumbnailErrors(app, message, i) {
          return this.VideoInfoErrors(app, message, i);
        }
        JobToDo(app, message, i) {
          const total = message.notification.total;
          const label = message.notification.name;
          const title = message.notification.title;
          if (title) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("strong", null, title));
          } else if (total) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, tr("To load"), ":", " ", /*#__PURE__*/React.createElement("strong", null, total, " ", label));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, tr("To load"), ": ", tr("nothing!")));
          }
        }
        NbMiniatures(app, message, i) {
          const total = message.notification.total;
          if (total) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("strong", null, tr("{count} miniature(s) saved.", {
              count: total
            })));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, tr("No miniatures saved!")));
          }
        }
        Message(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, Characters.WARNING_SIGN), " ", message.notification.message);
        }
      };
      ACTIONS = {
        update_database: "Update database",
        find_similar_videos: "Find similarities",
        find_similar_videos_ignore_cache: "Find similarities (ignore cache)",
        create_database: "Create database",
        open_database: "Open database",
        move_video_file: "Move video file"
      };
      _export("HomePage", HomePage = class HomePage extends React.Component {
        constructor(props) {
          // parameters: {command: [name, ...args]}
          // app: App
          super(props);
          this.state = {
            loaded: false,
            ready: false,
            status: null,
            messages: [],
            jobMap: new Map()
          };
          this.notify = this.notify.bind(this);
          this.onDatabaseReady = this.onDatabaseReady.bind(this);
          this.onDone = this.onDone.bind(this);
          this.onCancelled = this.onCancelled.bind(this);
          this.onEnd = this.onEnd.bind(this);
          this.onJobToDo = this.onJobToDo.bind(this);
          this.onJobStep = this.onJobStep.bind(this);
          this.onProfilingEnd = this.onProfilingEnd.bind(this);
          this.collectEndNotification = this.collectEndNotification.bind(this);
          this.collectNotification = this.collectNotification.bind(this);
          this.computeCollectedNotification = this.computeCollectedNotification.bind(this);
        }
        render() {
          return /*#__PURE__*/React.createElement("div", {
            id: "home",
            className: "absolute-plain p-4 vertical"
          }, /*#__PURE__*/React.createElement("div", {
            className: "text-center p-2"
          }, this.renderInitialButton()), /*#__PURE__*/React.createElement("div", {
            id: "notifications",
            className: "notifications flex-grow-1 overflow-auto"
          }, this.renderMessages()));
        }
        renderInitialButton() {
          if (this.props.parameters.onReady) return /*#__PURE__*/React.createElement("strong", null, this.state.status || ACTIONS[this.props.parameters.command[0]] + " ...");else if (this.state.loaded) return /*#__PURE__*/React.createElement("button", {
            onClick: () => this.props.app.loadVideosPage()
          }, tr("Display videos"));else return /*#__PURE__*/React.createElement("button", {
            disabled: true
          }, ACTIONS[this.props.parameters.command[0]], " ...");
        }
        renderMessages() {
          const output = this.state.messages.map((message, i) => /*#__PURE__*/React.createElement(NotificationRenderer, {
            app: this,
            message: message,
            i: i,
            key: i
          }));
          if (!this.state.loaded) output.push(/*#__PURE__*/React.createElement("div", {
            key: this.state.messages.length
          }, "..."));
          return output;
        }
        componentDidMount() {
          NOTIFICATION_MANAGER.installFrom(this);
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
          NOTIFICATION_MANAGER.uninstallFrom(this);
        }
        notify(notification) {
          this.collectNotification(notification);
        }
        onDatabaseReady(notification) {
          this.collectEndNotification(notification);
        }
        onDone(notification) {
          this.collectEndNotification(notification);
        }
        onCancelled(notification) {
          this.collectEndNotification(notification);
        }
        onEnd(notification) {
          this.collectEndNotification(notification);
        }
        onJobToDo(notification) {
          this.setState(prevState => {
            const name = notification.notification.name;
            const total = notification.notification.total;
            const jobMap = new Map(prevState.jobMap.entries());
            jobMap.set(name, new ProgressionMonitoring(name, total));
            return this.computeCollectedNotification(prevState, notification, {
              jobMap
            });
          });
        }
        onJobStep(notification) {
          this.setState(prevState => {
            const previousMap = prevState.jobMap;
            const jobsAreAlreadyCollected = previousMap.get(notification.notification.name).jobs.size;
            const jobMap = new Map(previousMap.entries());
            jobMap.get(notification.notification.name).collectJobStep(notification);
            return this.computeCollectedNotification(prevState, notification, {
              jobMap
            }, !jobsAreAlreadyCollected);
          });
        }
        onProfilingEnd(notification) {
          this.setState(prevState => {
            const messages = prevState.messages.slice();
            const lastIndex = messages.length - 1;
            if (messages.length && messages[lastIndex].name === "ProfilingStart" && messages[lastIndex].notification.name === notification.notification.name) {
              messages.pop();
              notification.notification.inplace = true;
            }
            messages.push(notification);
            return {
              messages
            };
          });
        }
        collectEndNotification(notification) {
          const name = notification.name;
          this.collectNotification(notification, {
            loaded: name,
            status: EndStatus[name],
            ready: EndReady[name]
          });
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
          this.setState(prevState => this.computeCollectedNotification(prevState, notification, updates, store));
        }

        /**
         * Callback to return new state based on previous state.
         * Useful to enqueue successive state updates, waiting from previous update
         * to be applied and then accessing to an up-to-date state.
         * Necessary because notification management seems asynchronous,
         * so, a notification callback may not have access to updated state.
         */
        computeCollectedNotification(prevState, notification, updates = {}, store = true) {
          if (store) {
            const messages = prevState.messages.slice();
            messages.push(notification);
            updates.messages = messages;
          }
          return updates;
        }
      });
      HomePage.propTypes = {
        app: PropTypes.object.isRequired,
        parameters: PropTypes.shape({
          command: PropTypes.array.isRequired,
          // onReady(notificationName)
          onReady: PropTypes.func
        })
      };
    }
  };
});