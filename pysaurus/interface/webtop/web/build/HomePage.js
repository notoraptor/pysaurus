System.register(["./constants.js"], function (_export, _context) {
  "use strict";

  var HomeStatus, ProgressionMonitoring, HomePage, NotificationCollector, NotificationMessenger;

  function collectNotification(app, notification, updates, store = true) {
    if (store) {
      const messages = app.state.messages.slice();
      messages.push(notification);
      updates.messages = messages;
    }

    app.setState(updates);
  }

  function generateMonitoringMessage(monitoring, name, i) {
    const total = monitoring.total;
    let current = 0;

    for (let jobId of Object.keys(monitoring.jobs)) {
      current += monitoring.jobs[jobId];
    }

    const percent = Math.round(current * 100 / total);
    const s0 = name + "-job";
    const s1 = "job horizontal " + s0;
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: s1
    }, /*#__PURE__*/React.createElement("label", {
      htmlFor: s0,
      className: "info"
    }, current, " / ", total, " (", percent, " %)"), /*#__PURE__*/React.createElement("progress", {
      id: s0,
      value: current,
      max: total
    }));
  }

  _export("HomePage", void 0);

  return {
    setters: [function (_constantsJs) {
      HomeStatus = _constantsJs.HomeStatus;
    }],
    execute: function () {
      ProgressionMonitoring = class ProgressionMonitoring {
        constructor() {
          this.total = 0;
          this.jobs = {};
        }

        clone(total = undefined, jobs = undefined) {
          const copy = new ProgressionMonitoring();
          copy.total = total ? total : this.total;
          copy.jobs = jobs ? jobs : this.jobs;
          return copy;
        }

        collectJobNotification(notification) {
          this.jobs[notification.notification.index] = notification.notification.parsed;
          return this.clone();
        }

      };
      NotificationCollector = {
        DatabaseReady: function (app, notification) {
          collectNotification(app, notification, {
            status: HomeStatus.LOADED
          });
        },
        VideosToLoad: function (app, notification) {
          collectNotification(app, notification, {
            videosMonitoring: app.state.videosMonitoring.clone(notification.notification.total)
          });
        },
        ThumbnailsToLoad: function (app, notification) {
          collectNotification(app, notification, {
            thumbnailsMonitoring: app.state.thumbnailsMonitoring.clone(notification.notification.total)
          });
        },
        MiniaturesToLoad: function (app, notification) {
          collectNotification(app, notification, {
            miniaturesMonitoring: app.state.miniaturesMonitoring.clone(notification.notification.total)
          });
        },
        VideoJob: function (app, notification) {
          collectNotification(app, notification, {
            videosMonitoring: app.state.videosMonitoring.collectJobNotification(notification)
          }, !app.state.messages.length || app.state.messages[app.state.messages.length - 1].name !== notification.name);
        },
        ThumbnailJob: function (app, notification) {
          collectNotification(app, notification, {
            thumbnailsMonitoring: app.state.thumbnailsMonitoring.collectJobNotification(notification)
          }, !app.state.messages.length || app.state.messages[app.state.messages.length - 1].name !== notification.name);
        },
        MiniatureJob: function (app, notification) {
          collectNotification(app, notification, {
            miniaturesMonitoring: app.state.miniaturesMonitoring.collectJobNotification(notification)
          }, !app.state.messages.length || app.state.messages[app.state.messages.length - 1].name !== notification.name);
        },
        // notifications ignored.
        ProfilingStart: function (app, notification) {}
      };
      NotificationMessenger = {
        VideoJob: function (app, message, i) {
          return generateMonitoringMessage(app.state.videosMonitoring, 'video', i);
        },
        ThumbnailJob: function (app, message, i) {
          return generateMonitoringMessage(app.state.thumbnailsMonitoring, 'thumb', i);
        },
        MiniatureJob: function (app, message, i) {
          return generateMonitoringMessage(app.state.miniaturesMonitoring, 'miniature', i);
        },
        DatabaseLoaded: function (app, message, i) {
          const data = message.notification;
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Database ", message.name === 'DatabaseSaved' ? 'saved' : 'loaded'), ":", data.entries, ' ', data.entries > 1 ? 'entries' : 'entry', ",", data.discarded, " discarded,", data.unreadable_not_found, " unreadable not found,", data.unreadable_found, " unreadable found,", data.readable_not_found, " readable not found,", data.readable_found_without_thumbnails, " readable found without thumbnails,", data.valid, " valid");
        },
        DatabaseSaved: function (app, message, i) {
          return NotificationMessenger.DatabaseLoaded(app, message, i);
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
        ProfilingEnd: function (app, message, i) {
          if (i > 0 && ['VideoJob', 'ThumbnailJob', 'MiniatureJob'].indexOf(app.state.messages[i - 1].name) !== -1) return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("strong", null, "Loaded"), " in ", message.notification.time);
        },
        VideoInfoErrors: function (app, message, i) {
          const errors = message.notification.video_errors;
          const keys = Object.keys(errors);
          keys.sort();
          return /*#__PURE__*/React.createElement("div", {
            key: i
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, errors.length, ' ', message.name === 'VideoInfoErrors' ? 'video' : 'thumbnail', "error", errors.length > 1 ? 's' : ''), ":"), /*#__PURE__*/React.createElement("ul", null, keys.map((name, indexName) => /*#__PURE__*/React.createElement("li", {
            key: indexName
          }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("code", null, name)), /*#__PURE__*/React.createElement("ul", null, errors[name].map((error, indexError) => /*#__PURE__*/React.createElement("li", {
            key: indexError
          }, /*#__PURE__*/React.createElement("code", null, error))))))));
        },
        VideoThumbnailErrors: function (app, message, i) {
          return NotificationMessenger.VideoInfoErrors(app, message, i);
        },
        VideosToLoad: function (app, message, i) {
          const labels = {
            VideosToLoad: 'video',
            ThumbnailsToLoad: 'thumbnail',
            MiniaturesToLoad: 'miniature'
          };
          const total = message.notification.total;
          const label = labels[message.name];

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
        ThumbnailsToLoad: function (app, message, i) {
          return NotificationMessenger.VideosToLoad(app, message, i);
        },
        MiniaturesToLoad: function (app, message, i) {
          return NotificationMessenger.VideosToLoad(app, message, i);
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
          // parameters: {}
          // app: App
          super(props);
          this.state = {
            status: this.props.parameters.update ? HomeStatus.LOADING : HomeStatus.INITIAL,
            messages: [],
            videosMonitoring: new ProgressionMonitoring(),
            thumbnailsMonitoring: new ProgressionMonitoring(),
            miniaturesMonitoring: new ProgressionMonitoring(),
            update: false
          };
          this.callbackIndex = -1;
          this.notify = this.notify.bind(this);
          this.loadDatabase = this.loadDatabase.bind(this);
          this.displayVideos = this.displayVideos.bind(this);
          this.onChangeUpdate = this.onChangeUpdate.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            id: "home"
          }, /*#__PURE__*/React.createElement("div", {
            className: "button-initial"
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
          if (status === HomeStatus.INITIAL) return /*#__PURE__*/React.createElement("button", {
            onClick: this.loadDatabase
          }, "Load database");
          if (status === HomeStatus.LOADING) return /*#__PURE__*/React.createElement("button", {
            disabled: true
          }, this.props.parameters.update ? 'Updating' : 'Loading', " database ...");
          if (status === HomeStatus.LOADED) return /*#__PURE__*/React.createElement("button", {
            onClick: this.displayVideos
          }, "Display videos");
        }

        renderMessages() {
          const output = [];
          let ready = false;

          for (let i = 0; i < this.state.messages.length; ++i) {
            const message = this.state.messages[i];
            const name = message.name;
            ready = name === 'DatabaseReady' && i === this.state.messages.length - 1;
            let display = null;

            if (NotificationMessenger[name]) {
              display = NotificationMessenger[name](this, message, i);
              if (display) output.push(display);
            } else {
              output.push( /*#__PURE__*/React.createElement("div", {
                key: i
              }, /*#__PURE__*/React.createElement("em", null, "unknown"), ": ", message.message));
            }
          }

          if (!ready && this.status === HomeStatus.LOADING) output.push( /*#__PURE__*/React.createElement("div", {
            key: this.state.messages.length
          }, "..."));
          return output;
        }

        componentDidMount() {
          this.callbackIndex = Notifications.register(this.notify);
          if (this.props.parameters.update) python_call('update_database');
        }

        componentWillUnmount() {
          Notifications.unregister(this.callbackIndex);
        }

        notify(notification) {
          const name = notification.name;
          if (NotificationCollector[name]) return NotificationCollector[name](this, notification);else collectNotification(this, notification, {});
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

      });
    }
  };
});