System.register(["./App.js", "./utils/Callbacks.js", "./utils/NotificationManager.js", "./utils/backend.js"], function (_export, _context) {
  "use strict";

  var App, Callbacks, NotificationManager, Backend;
  return {
    setters: [function (_AppJs) {
      App = _AppJs.App;
    }, function (_utilsCallbacksJs) {
      Callbacks = _utilsCallbacksJs.Callbacks;
    }, function (_utilsNotificationManagerJs) {
      NotificationManager = _utilsNotificationManagerJs.NotificationManager;
    }, function (_utilsBackendJs) {
      Backend = _utilsBackendJs.Backend;
    }],
    execute: function () {
      /** NOTIFICATION_MANAGER.call is called from Python to send notifications to interface. */
      window.NOTIFICATION_MANAGER = new NotificationManager();

      /** Global keyboard manager. Used to react on shortcuts. */
      window.KEYBOARD_MANAGER = new Callbacks();
      window.onkeydown = function (event) {
        KEYBOARD_MANAGER.call(event);
      };
      if (!window.QT) {
        document.body.onunload = function () {
          console.info("GUI closed!");
          Backend.close_app();
        };
      }
      backend_call("get_constants", []).then(constants => {
        for (let entry of Object.entries(constants)) {
          const [name, value] = entry;
          window[name] = value;
          // console.log(["CONSTANT", name, value]);
        }
        const root = ReactDOM.createRoot(document.getElementById("root"));
        root.render(/*#__PURE__*/React.createElement(App, null));
      });
    }
  };
});