System.register(["./App.js", "./utils/backend.js"], function (_export, _context) {
  "use strict";

  var App, python_call;
  return {
    setters: [function (_AppJs) {
      App = _AppJs.App;
    }, function (_utilsBackendJs) {
      python_call = _utilsBackendJs.python_call;
    }],
    execute: function () {
      window.onkeydown = function (event) {
        KEYBOARD_MANAGER.call(event);
      };

      document.body.onunload = function () {
        console.info('GUI closed!');
        python_call('close_app');
      };

      ReactDOM.render( /*#__PURE__*/React.createElement(App, null), document.getElementById('root'));
    }
  };
});