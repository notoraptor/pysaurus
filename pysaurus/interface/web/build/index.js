System.register(["./App.js", "./utils/Callbacks.js", "./utils/backend.js", "./utils/NotificationManager.js"], function (_export, _context) {
  "use strict";

  var App, Callbacks, python_call, NotificationManager;
  return {
    setters: [function (_AppJs) {
      App = _AppJs.App;
    }, function (_utilsCallbacksJs) {
      Callbacks = _utilsCallbacksJs.Callbacks;
    }, function (_utilsBackendJs) {
      python_call = _utilsBackendJs.python_call;
    }, function (_utilsNotificationManagerJs) {
      NotificationManager = _utilsNotificationManagerJs.NotificationManager;
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
          python_call("close_app");
        };
      }

      backend_call("get_constants", []).then(constants => {
        for (let entry of Object.entries(constants)) {
          const [name, value] = entry;
          window[name] = value; // console.log(`${name}: ${value}`);
        }

        ReactDOM.render( /*#__PURE__*/React.createElement(App, null), document.getElementById("root"));
      });
    }
  };
});