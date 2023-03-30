System.register(["../language.js", "./globals.js"], function (_export, _context) {
  "use strict";

  var LangContext, APP_STATE, FancyboxManager, Fancybox;
  return {
    setters: [function (_languageJs) {
      LangContext = _languageJs.LangContext;
    }, function (_globalsJs) {
      APP_STATE = _globalsJs.APP_STATE;
    }],
    execute: function () {
      FancyboxManager = class FancyboxManager {
        constructor(containerID) {
          this.containerID = containerID;
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
          ReactDOM.render( /*#__PURE__*/React.createElement(LangContext.Provider, {
            value: APP_STATE.lang
          }, component), document.getElementById(this.containerID));
        }
        close() {
          this.loaded = false;
          this.manageOtherActiveElements();
          ReactDOM.unmountComponentAtNode(document.getElementById(this.containerID));
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