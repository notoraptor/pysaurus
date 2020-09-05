System.register(["./Test.js", "./HomePage.js", "./VideosPage.js", "./PropertiesPage.js", "./ClassificationPage.js", "./FancyBox.js", "./constants.js"], function (_export, _context) {
  "use strict";

  var Test, HomePage, VideosPage, PropertiesPage, ClassificationPage, FancyBox, FIELDS, PAGE_SIZES, VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER, App;

  _export("App", void 0);

  return {
    setters: [function (_TestJs) {
      Test = _TestJs.Test;
    }, function (_HomePageJs) {
      HomePage = _HomePageJs.HomePage;
    }, function (_VideosPageJs) {
      VideosPage = _VideosPageJs.VideosPage;
    }, function (_PropertiesPageJs) {
      PropertiesPage = _PropertiesPageJs.PropertiesPage;
    }, function (_ClassificationPageJs) {
      ClassificationPage = _ClassificationPageJs.ClassificationPage;
    }, function (_FancyBoxJs) {
      FancyBox = _FancyBoxJs.FancyBox;
    }, function (_constantsJs) {
      FIELDS = _constantsJs.FIELDS;
      PAGE_SIZES = _constantsJs.PAGE_SIZES;
      VIDEO_DEFAULT_PAGE_SIZE = _constantsJs.VIDEO_DEFAULT_PAGE_SIZE;
      VIDEO_DEFAULT_PAGE_NUMBER = _constantsJs.VIDEO_DEFAULT_PAGE_NUMBER;
    }],
    execute: function () {
      _export("App", App = class App extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            page: "home",
            parameters: {},
            fancy: null
          };
          this.manageFancyBoxView = this.manageFancyBoxView.bind(this);
          this.onCloseFancyBox = this.onCloseFancyBox.bind(this);
          this.loadPage = this.loadPage.bind(this);
          this.loadDialog = this.loadDialog.bind(this);
          this.loadVideosPage = this.loadVideosPage.bind(this);
          this.loadPropertiesPage = this.loadPropertiesPage.bind(this);
          APP = this;
        }

        render() {
          const fancy = this.state.fancy;
          return /*#__PURE__*/React.createElement("div", {
            className: "app"
          }, /*#__PURE__*/React.createElement("main", null, this.renderPage()), fancy ? this.renderFancyBox() : '');
        }

        renderPage() {
          const parameters = this.state.parameters;
          const page = this.state.page;
          if (page === "test") return /*#__PURE__*/React.createElement(Test, {
            app: this,
            parameters: parameters
          });
          if (page === "home") return /*#__PURE__*/React.createElement(HomePage, {
            app: this,
            parameters: parameters
          });
          if (page === "videos") return /*#__PURE__*/React.createElement(VideosPage, {
            app: this,
            parameters: parameters
          });
          if (page === "properties") return /*#__PURE__*/React.createElement(PropertiesPage, {
            app: this,
            parameters: parameters
          });
          if (page === "classification") return /*#__PURE__*/React.createElement(ClassificationPage, {
            app: this,
            parameters: parameters
          });
        }

        renderFancyBox() {
          const fancy = this.state.fancy;
          return /*#__PURE__*/React.createElement(FancyBox, {
            title: fancy.title,
            onBuild: fancy.onBuild,
            onClose: fancy.onClose
          });
        }

        updateApp(state) {
          this.setState(state, this.manageFancyBoxView);
        }

        manageFancyBoxView() {
          const focusableElements = [...document.querySelector(".app main").querySelectorAll('a, button, input, textarea, select, details, [tabindex]:not([tabindex="-1"])')].filter(el => !el.hasAttribute('disabled'));

          for (let element of focusableElements) {
            if (this.state.fancy) {
              // If activated, deactivate and mark as deactivated.
              if (!element.getAttribute("disabled")) {
                const tabIndex = element.tabIndex;
                element.tabIndex = "-1";
                element.setAttribute("fancy", tabIndex);
              }
            } else {
              // Re-activate elements marked as deactivated.
              if (element.hasAttribute("fancy")) {
                element.tabIndex = element.getAttribute("fancy");
                element.removeAttribute("fancy");
              }
            }
          }
        }

        onCloseFancyBox() {
          this.updateApp({
            fancy: null
          });
        } // Public methods for children components.


        loadPage(pageName, parameters = undefined) {
          parameters = parameters ? parameters : {};
          this.updateApp({
            page: pageName,
            parameters: parameters
          });
        }

        loadDialog(title, onBuild) {
          if (this.state.fancy) throw "a fancy box is already displayed.";
          this.updateApp({
            fancy: {
              title: title,
              onClose: this.onCloseFancyBox,
              onBuild: onBuild
            }
          });
        }

        loadVideosPage(pageSize = undefined, pageNumber = undefined, videoFields = undefined) {
          if (pageSize === undefined) pageSize = VIDEO_DEFAULT_PAGE_SIZE;
          if (pageNumber === undefined) pageNumber = VIDEO_DEFAULT_PAGE_NUMBER;
          if (videoFields === undefined) videoFields = FIELDS;
          python_call('get_info_and_videos', pageSize, pageNumber, videoFields).then(info => {
            this.loadPage("videos", {
              pageSize: pageSize,
              pageNumber: pageNumber,
              info: info
            });
          }).catch(backend_error);
        }

        loadPropertiesPage() {
          python_call('get_prop_types').then(definitions => this.loadPage("properties", {
            definitions: definitions
          })).catch(backend_error);
        }

        loadClassificationPage(data) {
          this.loadPage("classification", data);
        }

      });
    }
  };
});