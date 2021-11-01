System.register(["../utils/constants.js", "../utils/backend.js", "../language.js"], function (_export, _context) {
  "use strict";

  var Characters, backend_error, python_call, LangContext, ProgressionMonitoring, Monitoring, NotificationRenderer, HomePage, EndStatus, EndReady, NotificationCollector, ACTIONS;

  function collectEndNotification(app, notification) {
    const name = notification.name;
    app.collectNotification(notification, {
      loaded: name,
      status: EndStatus[name],
      ready: EndReady[name]
    });
  }

  _export("HomePage", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      Characters = _utilsConstantsJs.Characters;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
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
          const title = monitoring.title || this.context.text_done.format({
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
      Monitoring.contextType = LangContext;
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
      NotificationCollector = {
        DatabaseReady: collectEndNotification,
        Done: collectEndNotification,
        Cancelled: collectEndNotification,
        End: collectEndNotification,
        JobToDo: function (app, notification) {
          const name = notification.notification.name;
          const total = notification.notification.total;
          const jobMap = new Map(app.state.jobMap);
          jobMap.set(name, new ProgressionMonitoring(name, total));
          app.collectNotification(notification, {
            jobMap
          });
        },
        JobStep: function (app, notification) {
          const lastIndex = app.state.messages.length - 1;
          const jobsAreAlreadyCollected = app.state.jobMap.get(notification.notification.name).jobs.size;
          const jobMap = new Map(app.state.jobMap);
          jobMap.get(notification.notification.name).collectJobStep(notification);
          app.collectNotification(notification, {
            jobMap
          }, !jobsAreAlreadyCollected);
        },
        ProfilingEnd: function (app, notification) {
          const messages = app.state.messages.slice();
          const lastIndex = messages.length - 1;

          if (messages.length && messages[lastIndex].name === "ProfilingStart" && messages[lastIndex].notification.name === notification.notification.name) {
            messages.pop();
            notification.notification.inplace = true;
          }

          messages.push(notification);
          app.setState({
            messages
          });
        }
      };
      NotificationRenderer = class NotificationRenderer extends React.Component {
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
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, this.context.text_notification_unknown), ": ", message.message);
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
          }, /*#__PURE__*/React.createElement("strong", null, message.name === 'DatabaseSaved' ? this.context.text_database_saved : this.context.text_database_loaded), ":", this.context.text_nb_entries.format({
            count: data.entries
          }) + ", ", this.context.text_nb_discarded.format({
            count: data.discarded
          }) + ", ", this.context.text_nb_unreadable_not_found.format({
            count: data.unreadable_not_found
          }) + ", ", this.context.text_nb_unreadable_found.format({
            count: data.unreadable_found
          }) + ", ", this.context.text_nb_readable_not_found.format({
            count: data.readable_not_found
          }) + ", ", this.context.text_nb_readable_found_without_thumbnails.format({
            count: data.readable_found_without_thumbnails
          }) + ", ", this.context.text_nb_valid.format({
            count: data.valid
          }));
        }

        DatabaseSaved(app, message, i) {
          return this.DatabaseLoaded(app, message, i);
        }

        DatabaseReady(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, this.context.text_notification_database_ready));
        }

        Done(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, this.context.text_notification_done));
        }

        Cancelled(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, this.context.text_notification_cancelled));
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
          }, this.context.gui_home_collected_files.format({
            count
          }).markdown(true));
        }

        MissingThumbnails(app, message, i) {
          const names = message.notification.names;

          if (names.length) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, this.context.text_notification_missing_thumbnails.format({
              count: names.length
            })), ":"), names.map((name, indexName) => /*#__PURE__*/React.createElement("div", {
              key: indexName
            }, /*#__PURE__*/React.createElement("code", null, name))));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, this.context.text_notification_no_missing_thumbnails));
          }
        }

        ProfilingStart(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, this.context.text_profiling), " ", message.notification.name);
        }

        ProfilingEnd(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, message.notification.inplace ? `${this.context.text_profiling} / ` : "", this.context.text_profiled), " ", message.notification.name, " ", /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, "TIME"), " ", message.notification.time);
        }

        VideoInfoErrors(app, message, i) {
          const errors = message.notification.video_errors;
          const keys = Object.keys(errors);
          keys.sort();
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, (message.name === 'VideoInfoErrors' ? this.context.text_nb_video_errors : this.context.text_nb_thumbnail_errors).format({
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
            }, this.context.gui_home_to_load, ": ", /*#__PURE__*/React.createElement("strong", null, total, " ", label));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, this.context.gui_home_to_load, ": ", this.context.text_nothing));
          }
        }

        NbMiniatures(app, message, i) {
          const total = message.notification.total;

          if (total) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("strong", null, this.context.text_nb_miniatures_saved.format({
              count: total
            })));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, this.context.text_no_miniatures_saved));
          }
        }

        Message(app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, Characters.WARNING_SIGN), " ", message.notification.message);
        }

      };
      NotificationRenderer.contextType = LangContext;
      ACTIONS = {
        update_database: "Update database",
        find_similar_videos: "Find similarities",
        find_similar_videos_ignore_cache: "Find similarities (ignore cache)",
        create_database: "Create database",
        open_database: "Open database",
        move_video_file: "Move video file",
        compute_predictor: "Compute predictor",
        apply_predictor: "Predict"
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
          this.callbackIndex = -1;
          this.notify = this.notify.bind(this);
          this.displayVideos = this.displayVideos.bind(this);
          this.collectNotification = this.collectNotification.bind(this);
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
            onClick: this.displayVideos
          }, this.context.text_display_videos);else return /*#__PURE__*/React.createElement("button", {
            disabled: true
          }, ACTIONS[this.props.parameters.command[0]], " ...");
        }

        renderMessages() {
          const output = this.state.messages.map((message, i) => /*#__PURE__*/React.createElement(NotificationRenderer, {
            app: this,
            message: message,
            i: i
          }));
          if (!this.state.loaded) output.push( /*#__PURE__*/React.createElement("div", {
            key: this.state.messages.length
          }, "..."));
          return output;
        }

        componentDidMount() {
          this.callbackIndex = NOTIFICATION_MANAGER.register(this.notify);
          python_call(...this.props.parameters.command).catch(backend_error);
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
          if (NotificationCollector[name]) return NotificationCollector[name](this, notification);else this.collectNotification(notification);
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

      });

      HomePage.contextType = LangContext;
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