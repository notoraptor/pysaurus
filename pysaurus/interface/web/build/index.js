System.register(["./App.js", "./utils/Callbacks.js", "./utils/backend.js"], function (_export, _context) {
  "use strict";

  var App, Callbacks, python_call;
  return {
    setters: [function (_AppJs) {
      App = _AppJs.App;
    }, function (_utilsCallbacksJs) {
      Callbacks = _utilsCallbacksJs.Callbacks;
    }, function (_utilsBackendJs) {
      python_call = _utilsBackendJs.python_call;
    }],
    execute: function () {
      /** NOTIFICATION_MANAGER.call is called from Python to send notifications to interface. */
      window.NOTIFICATION_MANAGER = new Callbacks();
      /** Global keyboard manager. Used to react on shortcuts. */

      window.KEYBOARD_MANAGER = new Callbacks();

      window.onkeydown = function (event) {
        KEYBOARD_MANAGER.call(event);
      };

      document.body.onunload = function () {
        console.info("GUI closed!");
        python_call("close_app");
      };

      ReactDOM.render( /*#__PURE__*/React.createElement(App, null), document.getElementById("root"));
    }
  };
});