System.register([], function (_export, _context) {
  "use strict";

  function python_call(name, ...args) {
    return window.backend_call(name, args);
  }

  function backend_error(error) {
    window.alert(PYTHON_LANG.backend_error.format({
      name: error.name,
      message: error.message
    }));
  }

  _export({
    python_call: python_call,
    backend_error: backend_error
  });

  return {
    setters: [],
    execute: function () {}
  };
});