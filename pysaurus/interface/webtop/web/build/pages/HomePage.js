System.register(["../utils/constants.js", "../utils/backend.js"], function (_export, _context) {
  "use strict";

  var Characters, HomeStatus, backend_error, python_call, ProgressionMonitoring, HomePage, NotificationCollector, NotificationRenderer, ACTIONS;

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
      Characters = _utilsConstantsJs.Characters;
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
        ProfilingStart: function (app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, "PROFILING"), " ", message.notification.name);
        },
        ProfilingEnd: function (app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, message.notification.inplace ? `PROFILING / ` : ``, "PROFILED"), " ", message.notification.name, " ", /*#__PURE__*/React.createElement("span", {
            className: "span-profiled"
          }, "TIME"), " ", message.notification.time);
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
        },
        Message: function (app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, Characters.WARNING_SIGN), " ", message.notification.message);
        }
      };
      ACTIONS = {
        update: {
          title: "Update database",
          name: "update_database"
        },
        similarities: {
          title: "Find similarities",
          name: "find_similar_videos"
        },
        similaritiesNoCache: {
          title: "Find similarities (ignore cache)",
          name: "find_similar_videos_ignore_cache"
        }
      };

      _export("HomePage", HomePage = class HomePage extends React.Component {
        constructor(props) {
          // parameters: {action: string = undefined}
          // app: App
          super(props);
          this.state = {
            status: this.props.parameters.action ? HomeStatus.LOADING : HomeStatus.INITIAL,
            messages: [],
            jobMap: new Map(),
            update: false,
            action: null
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
            id: "home",
            className: "vertical"
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
          const action = this.props.parameters.action;
          if (status === HomeStatus.INITIAL) return /*#__PURE__*/React.createElement("button", {
            onClick: this.loadDatabase
          }, "Load database");
          if (status === HomeStatus.LOADING) return /*#__PURE__*/React.createElement("button", {
            disabled: true
          }, action ? ACTIONS[action].title : `Loading database`, " ...");
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
          const action = this.props.parameters.action;

          if (action && ACTIONS.hasOwnProperty(action)) {
            python_call(ACTIONS[action].name);
          }
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

      HomePage.propTypes = {
        parameters: PropTypes.shape({
          action: PropTypes.string
        })
      };
    }
  };
});