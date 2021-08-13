System.register([], function (_export, _context) {
  "use strict";

  function python_call(name, ...args) {
    return new Promise((resolve, reject) => {
      python.call(name, args, resolve, reject);
    });
  }

  function backend_error(error) {
    window.alert(`Backend error: ${error.name}: ${error.message}`);
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