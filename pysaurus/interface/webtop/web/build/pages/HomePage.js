System.register(["../utils/constants.js", "../utils/backend.js"], function (_export, _context) {
  "use strict";

  var Characters, backend_error, python_call, ProgressionMonitoring, HomePage, EndStatus, EndReady, NotificationCollector, NotificationRenderer, ACTIONS;

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
    }, current, " done (", percent, " %)"), /*#__PURE__*/React.createElement("progress", {
      id: jobClassID,
      value: current,
      max: total
    }));
  }

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
        Done: function (app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Done!"));
        },
        Cancelled: function (app, message, i) {
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Cancelled."));
        },
        End: function (app, message, i) {
          const info = message.notification.message;
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Ended.", info ? ` ${info}` : ""));
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
          const title = message.notification.title;

          if (title) {
            return /*#__PURE__*/React.createElement("div", {
              key: i
            }, /*#__PURE__*/React.createElement("strong", null, title));
          } else if (total) {
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
          this.callbackIndex = -1;
          this.notify = this.notify.bind(this);
          this.displayVideos = this.displayVideos.bind(this);
          this.collectNotification = this.collectNotification.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            id: "home",
            className: "vertical"
          }, /*#__PURE__*/React.createElement("div", {
            className: "buttons"
          }, this.renderInitialButton()), /*#__PURE__*/React.createElement("div", {
            id: "notifications",
            className: "notifications"
          }, this.renderMessages()));
        }

        renderInitialButton() {
          if (this.props.parameters.onReady) return /*#__PURE__*/React.createElement("strong", null, this.state.status || ACTIONS[this.props.parameters.command[0]] + " ...");else if (this.state.loaded) return /*#__PURE__*/React.createElement("button", {
            onClick: this.displayVideos
          }, "Display videos");else return /*#__PURE__*/React.createElement("button", {
            disabled: true
          }, ACTIONS[this.props.parameters.command[0]], " ...");
        }

        renderMessages() {
          const output = [];

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