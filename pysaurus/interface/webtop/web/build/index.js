System.register(["./App.js"], function (_export, _context) {
  "use strict";

  var App;
  return {
    setters: [function (_AppJs) {
      App = _AppJs.App;
    }],
    execute: function () {
      ReactDOM.render( /*#__PURE__*/React.createElement(App, null), document.getElementById('root'));
    }
  };
});