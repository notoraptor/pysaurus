System.register([], function (_export, _context) {
  "use strict";

  var Exceptions;

  function createException(type, message) {
    return {
      type: type,
      message: message
    };
  }

  _export("Exceptions", void 0);

  return {
    setters: [],
    execute: function () {
      _export("Exceptions", Exceptions = class Exceptions {
        static fromErrorResponse(response) {
          return createException(response.error_type, response.message);
        }

        static disconnected() {
          return createException('disconnected', 'disconnected');
        }

        static connectionFailed() {
          return createException('connectionFailed', 'Unable to connect.');
        }

        static databaseFailed(message) {
          return createException('databaseFailed', message);
        }

      });
    }
  };
});