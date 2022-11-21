System.register([], function (_export, _context) {
  "use strict";

  var LangContext;

  /**
   * Translate text
   * @param text {string} - text to translate
   * @param placeholders {Object} - optional - map of values to use to format text
   * @returns {string} - text translated
   */
  function tr(text, placeholders = null) {
    if (placeholders !== null) text = text.format(placeholders);
    return text;
  }

  _export("tr", tr);

  return {
    setters: [],
    execute: function () {
      /** Interface language in a React context . **/
      _export("LangContext", LangContext = React.createContext({}));
    }
  };
});