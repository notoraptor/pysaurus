System.register(["../utils/constants.js", "../utils/backend.js"], function (_export, _context) {
  "use strict";

  var HomeStatus, backend_error, python_call, ProgressionMonitoring, HomePage, NotificationCollector, NotificationRenderer;

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
    return /*#__PURE__*/React.createElement("div", {
      className: `job horizontal ${jobClassID}`
    }, /*#__PURE__*/React.createElement("label", {
      htmlFor: jobClassID,
      className: "info"
    }, current, " / ", total, " (", percent, " %)"), /*#__PURE__*/React.createElement("progress", {
      id: jobClassID,
      value: current,
      max: total
    }));
  }

  _export("HomePage", void 0);

  return {
    setters: [function (_utilsConstantsJs) {
      HomeStatus = _utilsConstantsJs.HomeStatus;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }],
    execute: function () {
      ProgressionMonitoring = class ProgressionMonitoring {
        constructor(name, total) {
          this.name = name;
          this.total = total;
          this.jobs = new Map();
        }

        collectJobStep(notification) {
          this.jobs.set(notification.notification.channel, notification.notification.step);
        }

      };
      NotificationCollector = {
        DatabaseReady: function (app, notification) {
          app.collectNotification(notification, {
            status: HomeStatus.LOADED
          });
        },
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
          const jobIsBeingCollected = lastIndex > -1 && app.state.messages[lastIndex].name === notification.name && app.state.messages[lastIndex].notification.name === notification.notification.name;
          const jobMap = new Map(app.state.jobMap);
          jobMap.get(notification.notification.name).collectJobStep(notification);
          app.collectNotification(notification, {
            jobMap
          }, !jobIsBeingCollected);
        },
        // notifications ignored.
        ProfilingStart: function (app, notification) {}
      };
      NotificationRenderer = {
        JobStep: (app, message, i) => /*#__PURE__*/React.createElement(Monitoring, {
          monitoring: app.state.jobMap.get(message.notification.name),
          key: i
        }),
        DatabaseLoaded: function (app, message, i) {
          const data = message.notification;
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Database ", message.name === 'DatabaseSaved' ? 'saved' : 'loaded'), ":", data.entries, ' ', data.entries > 1 ? 'entries' : 'entry', ",", data.discarded, " discarded,", data.unreadable_not_found, " unreadable not found,", data.unreadable_found, " unreadable found,", data.readable_not_found, " readable not found,", data.readable_found_without_thumbnails, " readable found without thumbnails,", data.valid, " valid");
        },
        DatabaseSaved: function (app, message, i) {
          return NotificationRenderer.DatabaseLoaded(app, message, i);
        },
        DatabaseReady: function (app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Database open!"));
        },
        FinishedCollectingVideos: function (app, message, i) {
          const count = message.notification.count;
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Collected"), ' ', count, " file", count > 1 ? 's' : '');
        },
        MissingThumbnails: function (app, message, i) {
          const names = message.notification.names;

          if (names.length) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, "Missing ", names.length, " thumbnails"), ":"), names.map((name, indexName) => /*#__PURE__*/React.createElement("div", {
              key: indexName
            }, /*#__PURE__*/React.createElement("code", null, name))));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, "No missing thumbnails!"));
          }
        },
        ProfilingEnd: function (app, message, i) {// return (<div key={i}><strong>Loaded</strong> in {message.notification.time}</div>);
        },
        VideoInfoErrors: function (app, message, i) {
          const errors = message.notification.video_errors;
          const keys = Object.keys(errors);
          keys.sort();
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, errors.length, ' ', message.name === 'VideoInfoErrors' ? 'video' : 'thumbnail', " ", "error", errors.length > 1 ? 's' : ''), ":"), /*#__PURE__*/React.createElement("ul", null, keys.map((name, indexName) => /*#__PURE__*/React.createElement("li", {
            key: indexName
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("code", null, name)), /*#__PURE__*/React.createElement("ul", null, errors[name].map((error, indexError) => /*#__PURE__*/React.createElement("li", {
            key: indexError
          }, /*#__PURE__*/React.createElement("code", null, error))))))));
        },
        VideoThumbnailErrors: function (app, message, i) {
          return NotificationRenderer.VideoInfoErrors(app, message, i);
        },
        JobToDo: function (app, message, i) {
          const total = message.notification.total;
          const label = message.notification.name;

          if (total) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("strong", null, total, ' ', label, total > 1 ? 's' : '', " to load."));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, "No ", label, "s to load!"));
          }
        },
        NbMiniatures: function (app, message, i) {
          const total = message.notification.total;

          if (total) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("strong", null, total, " miniature", total > 1 ? 's' : '', " saved."));
          } else {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("em", null, "No miniatures saved!"));
          }
        }
      };

      _export("HomePage", HomePage = class HomePage extends React.Component {
        constructor(props) {
          // parameters: {update: bool = false}
          // app: App
          super(props);
          this.state = {
            status: this.props.parameters.update ? HomeStatus.LOADING : HomeStatus.INITIAL,
            messages: [],
            jobMap: new Map(),
            update: false
          };
          this.callbackIndex = -1;
          this.notify = this.notify.bind(this);
          this.loadDatabase = this.loadDatabase.bind(this);
          this.displayVideos = this.displayVideos.bind(this);
          this.onChangeUpdate = this.onChangeUpdate.bind(this);
          this.collectNotification = this.collectNotification.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            id: "home"
          }, /*#__PURE__*/React.createElement("div", {
            className: "buttons"
          }, this.state.status === HomeStatus.INITIAL ? /*#__PURE__*/React.createElement("span", {
            className: "input-update"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "update",
            checked: this.state.update,
            onChange: this.onChangeUpdate
          }), ' ', /*#__PURE__*/React.createElement("label", {
            htmlFor: "update"
          }, "Update on load")) : '', this.renderInitialButton()), /*#__PURE__*/React.createElement("div", {
            className: "notifications"
          }, this.renderMessages()));
        }

        renderInitialButton() {
          const status = this.state.status;
          const update = this.props.parameters.update;
          if (status === HomeStatus.INITIAL) return /*#__PURE__*/React.createElement("button", {
            onClick: this.loadDatabase
          }, "Load database");
          if (status === HomeStatus.LOADING) return /*#__PURE__*/React.createElement("button", {
            disabled: true
          }, update ? 'Updating' : 'Loading', " database ...");
          if (status === HomeStatus.LOADED) return /*#__PURE__*/React.createElement("button", {
            onClick: this.displayVideos
          }, "Display videos");
        }

        renderMessages() {
          const output = [];
          const lastIndex = this.state.messages.length - 1;

          for (let i = 0; i < this.state.messages.length; ++i) {
            const message = this.state.messages[i];
            const name = message.name;

            if (NotificationRenderer[name]) {
              const display = NotificationRenderer[name](this, message, i);
              if (display) output.push(display);
            } else {
              output.push( /*#__PURE__*/React.createElement("div", {
                key: i
              }, /*#__PURE__*/React.createElement("em", null, "unknown"), ": ", message.message));
            }
          }

          const ready = lastIndex > -1 && this.state.messages[lastIndex].name === "DatabaseReady";
          if (!ready && this.status === HomeStatus.LOADING) output.push( /*#__PURE__*/React.createElement("div", {
            key: this.state.messages.length
          }, "..."));
          return output;
        }

        componentDidMount() {
          this.callbackIndex = NOTIFICATION_MANAGER.register(this.notify);
          if (this.props.parameters.update) python_call('update_database');
        }

        componentWillUnmount() {
          NOTIFICATION_MANAGER.unregister(this.callbackIndex);
        }

        notify(notification) {
          const name = notification.name;
          if (NotificationCollector[name]) return NotificationCollector[name](this, notification);else this.collectNotification(notification);
        }

        loadDatabase() {
          python_call('load_database', this.state.update).then(() => {
            this.setState({
              status: HomeStatus.LOADING
            });
          }).catch(backend_error);
        }

        displayVideos() {
          this.props.app.loadVideosPage();
        }

        onChangeUpdate(event) {
          this.setState({
            update: event.target.checked
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
          if (store) {
            const messages = this.state.messages.slice();
            messages.push(notification);
            updates.messages = messages;
          }

          this.setState(updates);
        }

      });
    }
  };
});