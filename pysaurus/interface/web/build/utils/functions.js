System.register(["../language.js"], function (_export, _context) {
  "use strict";

  var tr, IdGenerator, Utilities, UTILITIES;
  function capitalizeFirstLetter(str) {
    if (str.length === 0) return str;
    if (str.length === 1) return str.toUpperCase();
    return str.substr(0, 1).toUpperCase() + str.substr(1);
  }

  /**
   *
   * @param text {string}
   * @param kwargs {Object}
   * @return string
   */
  function formatString(text, kwargs) {
    for (let entry of Object.entries(kwargs)) {
      const [key, value] = entry;
      text = text.replace(new RegExp("\\{" + key + "\\}", "g"), value.toString());
    }
    return text;
  }
  function arrayEquals(a, b) {
    return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((val, index) => val === b[index]);
  }

  /**
   * Compare two lists of video sources.
   * Each video source itself is a list of strings.
   * @param sources1 {Array<Array<string>>} - a list of video sources
   * @param sources2 {Array<Array<string>>} - another list of video sources
   * @returns {boolean} - true if source1 == source2
   */
  function compareSources(sources1, sources2) {
    if (sources1.length !== sources2.length) return false;
    for (let i = 0; i < sources1.length; ++i) {
      const path1 = sources1[i];
      const path2 = sources2[i];
      if (path1.length !== path2.length) return false;
      for (let j = 0; j < path1.length; ++j) {
        if (path1[j] !== path2[j]) return false;
      }
    }
    return true;
  }
  _export({
    capitalizeFirstLetter: capitalizeFirstLetter,
    formatString: formatString,
    IdGenerator: void 0,
    arrayEquals: arrayEquals,
    compareSources: compareSources
  });
  return {
    setters: [function (_languageJs) {
      tr = _languageJs.tr;
    }],
    execute: function () {
      _export("IdGenerator", IdGenerator = class IdGenerator {
        constructor() {
          this.id = 0;
        }
        next() {
          return ++this.id;
        }
      });
      Utilities = class Utilities {
        constructor() {
          this.parsePropValString = this.parsePropValString.bind(this);
        }

        /**
         * @param propType {string}
         * @param propEnum {Array}
         * @param value {string}
         * @returns {null}
         */
        parsePropValString(propType, propEnum, value) {
          let parsed = null;
          switch (propType) {
            case "bool":
              if (value === "false") parsed = false;else if (value === "true") parsed = true;else throw tr("Invalid bool value, expected: [false, true], got {value}", {
                value
              });
              break;
            case "int":
              parsed = parseInt(value);
              if (isNaN(parsed)) throw `Unable to parse integer: ${value}`;
              break;
            case "float":
              parsed = parseFloat(value);
              if (isNaN(parsed)) throw tr("Unable to parse floating value: {value}", {
                value
              });
              break;
            case "str":
              parsed = value;
              break;
            default:
              throw `Unknown property type: ${propType}`;
          }
          if (propEnum && propEnum.indexOf(parsed) < 0) throw tr("Invalid enum value, expected: [{expected}], got {value}", {
            expected: propEnum.join(", "),
            value: value
          });
          return parsed;
        }
      };
      _export("UTILITIES", UTILITIES = new Utilities());
    }
  };
});