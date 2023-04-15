System.register([], function (_export, _context) {
  "use strict";

  var FancyboxManager, Fancybox;
  return {
    setters: [],
    execute: function () {
      FancyboxManager = class FancyboxManager {
        constructor(containerID) {
          this.containerID = containerID;
          this.root = null;
          this.loaded = false;
          this.load = this.load.bind(this);
          this.close = this.close.bind(this);
          this.manageOtherActiveElements = this.manageOtherActiveElements.bind(this);
          this.isInactive = this.isInactive.bind(this);
        }
        static getFocusableElements() {
          return [...document.querySelector("main").querySelectorAll('a, button, input, textarea, select, details, [tabindex]:not([tabindex="-1"])')].filter(el => !el.hasAttribute("disabled"));
        }
        load(component) {
          if (this.loaded) throw "A fancy box is already displayed.";
          this.loaded = true;
          this.manageOtherActiveElements();
          this.root = ReactDOM.createRoot(document.getElementById(this.containerID));
          this.root.render(component);
        }
        close() {
          this.loaded = false;
          this.manageOtherActiveElements();
          this.root.unmount();
          this.root = null;
        }

        /**
         * Make sure all active elements are disabled if fancy box is displayed, and re-enabled when fancybox is closed.
         */
        manageOtherActiveElements() {
          if (this.loaded) {
            for (let element of FancyboxManager.getFocusableElements()) {
              // If activated, deactivate and mark as deactivated.
              if (!element.getAttribute("disabled")) {
                const tabIndex = element.tabIndex;
                element.tabIndex = "-1";
                element.setAttribute("fancy", tabIndex);
              }
            }
          } else {
            for (let element of FancyboxManager.getFocusableElements()) {
              // Re-activate elements marked as deactivated.
              if (element.hasAttribute("fancy")) {
                element.tabIndex = element.getAttribute("fancy");
                element.removeAttribute("fancy");
              }
            }
          }
        }
        isInactive() {
          return !this.loaded;
        }
      };
      /** Global fancybox manager. Used to open/close a fancybox. */
      _export("Fancybox", Fancybox = new FancyboxManager("fancybox"));
    }
  };
});