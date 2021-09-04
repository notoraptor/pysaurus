System.register([], function (_export, _context) {
  "use strict";

  var REQUEST_ID;

  function createRequest(name, parameters) {
    const request_id = REQUEST_ID;
    ++REQUEST_ID;
    return {
      request_id: request_id,
      name: name,
      parameters: parameters || {}
    };
  }

  _export("createRequest", createRequest);

  return {
    setters: [],
    execute: function () {
      REQUEST_ID = 0;
    }
  };
});