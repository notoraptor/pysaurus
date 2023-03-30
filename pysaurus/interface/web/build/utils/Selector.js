System.register([], function (_export, _context) {
  "use strict";

  var Selector;
  _export("Selector", void 0);
  return {
    setters: [],
    execute: function () {
      _export("Selector", Selector = class Selector {
        /**
         * @param other {Selector}
         */
        constructor(other = undefined) {
          this.all = other ? other.all : false;
          this.include = new Set(other ? other.include : []);
          this.exclude = new Set(other ? other.exclude : []);
        }
        clone() {
          return new Selector(this);
        }
        toJSON() {
          return {
            all: this.all,
            include: Array.from(this.include),
            exclude: Array.from(this.exclude)
          };
        }
        size(allSize) {
          return this.all ? allSize - this.exclude.size : this.include.size;
        }
        has(value) {
          return this.all && !this.exclude.has(value) || !this.all && this.include.has(value);
        }
        add(value) {
          if (this.all) {
            this.exclude.delete(value);
          } else {
            this.include.add(value);
          }
        }
        remove(value) {
          if (this.all) {
            this.exclude.add(value);
          } else {
            this.include.delete(value);
          }
        }
        clear() {
          this.all = false;
          this.include.clear();
          this.exclude.clear();
        }
        fill() {
          this.all = true;
          this.include.clear();
          this.exclude.clear();
        }
      });
    }
  };
});