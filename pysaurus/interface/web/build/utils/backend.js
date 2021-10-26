System.register(["./functions.js"], function (_export, _context) {
  "use strict";

  var formatString;

  function python_call(name, ...args) {
    return window.backend_call(name, args);
  }

  function backend_error(error) {
    window.alert(formatString(PYTHON_LANG.backend_error, {
      name: error.name,
      message: error.message
    }));
  }

  _export({
    python_call: python_call,
    backend_error: backend_error
  });

  return {
    setters: [function (_functionsJs) {
      formatString = _functionsJs.formatString;
    }],
    execute: function () {}
  };
});