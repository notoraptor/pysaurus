System.register(["./functions.js"], function (_export, _context) {
  "use strict";

  var IdGenerator, APP_STATE;
  return {
    setters: [function (_functionsJs) {
      IdGenerator = _functionsJs.IdGenerator;
    }],
    execute: function () {
      /** Global state. **/
      _export("APP_STATE", APP_STATE = {
        videoHistory: new Set(),
        idGenerator: new IdGenerator(),
        latestMoveFolder: null,
        lang: null
      });
    }
  };
});