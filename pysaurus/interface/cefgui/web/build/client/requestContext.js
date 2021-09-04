System.register(["./future.js"], function (_export, _context) {
  "use strict";

  var Future, RequestContext;

  _export("RequestContext", void 0);

  return {
    setters: [function (_futureJs) {
      Future = _futureJs.Future;
    }],
    execute: function () {
      _export("RequestContext", RequestContext = class RequestContext {
        constructor(request) {
          this.request = request;
          this.future = new Future();
        }

        getRequestID() {
          return this.request.request_id;
        }

      });
    }
  };
});