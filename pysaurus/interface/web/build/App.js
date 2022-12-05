System.register(["./pages/Test.js", "./pages/HomePage.js", "./pages/VideosPage.js", "./pages/PropertiesPage.js", "./pages/DatabasesPage.js", "./utils/backend.js", "./utils/constants.js", "./language.js", "./utils/globals.js"], function (_export, _context) {
  "use strict";

  var Test, HomePage, VideosPage, PropertiesPage, DatabasesPage, backend_error, python_call, VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE, LangContext, APP_STATE, App;

  _export("App", void 0);

  return {
    setters: [function (_pagesTestJs) {
      Test = _pagesTestJs.Test;
    }, function (_pagesHomePageJs) {
      HomePage = _pagesHomePageJs.HomePage;
    }, function (_pagesVideosPageJs) {
      VideosPage = _pagesVideosPageJs.VideosPage;
    }, function (_pagesPropertiesPageJs) {
      PropertiesPage = _pagesPropertiesPageJs.PropertiesPage;
    }, function (_pagesDatabasesPageJs) {
      DatabasesPage = _pagesDatabasesPageJs.DatabasesPage;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_utilsConstantsJs) {
      VIDEO_DEFAULT_PAGE_NUMBER = _utilsConstantsJs.VIDEO_DEFAULT_PAGE_NUMBER;
      VIDEO_DEFAULT_PAGE_SIZE = _utilsConstantsJs.VIDEO_DEFAULT_PAGE_SIZE;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
    }, function (_utilsGlobalsJs) {
      APP_STATE = _utilsGlobalsJs.APP_STATE;
    }],
    execute: function () {
      _export("App", App = class App extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            page: null,
            parameters: {},
            lang: window.PYTHON_LANG,
            languages: []
          };
          APP_STATE.lang = this.state.lang;
          this.loadPage = this.loadPage.bind(this);
          this.loadPropertiesPage = this.loadPropertiesPage.bind(this);
          this.loadVideosPage = this.loadVideosPage.bind(this);
          this.getLanguages = this.getLanguages.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(LangContext.Provider, {
            value: this.state.lang
          }, this.renderPage());
        }

        renderPage() {
          const parameters = this.state.parameters;
          const page = this.state.page;
          if (!page) return "Opening ...";
          if (page === "test") return /*#__PURE__*/React.createElement(Test, {
            app: this,
            parameters: parameters
          });
          if (page === "databases") return /*#__PURE__*/React.createElement(DatabasesPage, {
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
        }

        componentDidMount() {
          if (!this.state.page) {
            python_call("get_app_state").then(appState => this.dbHome(appState)).catch(backend_error);
          }
        }

        loadPage(pageName, parameters = undefined, otherState = undefined) {
          parameters = parameters ? parameters : {};
          const state = Object.assign({}, otherState || {}, {
            page: pageName,
            parameters: parameters
          });
          this.setState(state);
        } // Public methods for children components.


        getLanguages() {
          return this.state.languages;
        }

        setLanguage(name) {
          python_call("set_language", name).then(lang => {
            APP_STATE.lang = lang;
            this.setState({
              lang
            });
          }).catch(backend_error);
        }

        dbHome(appState = undefined) {
          this.loadPage("databases", appState, appState ? {
            languages: appState.languages
          } : undefined);
        }

        dbUpdate(...command) {
          this.loadPage("home", {
            command
          });
        }

        loadVideosPage(pageSize = undefined, pageNumber = undefined) {
          if (pageSize === undefined) pageSize = VIDEO_DEFAULT_PAGE_SIZE;
          if (pageNumber === undefined) pageNumber = VIDEO_DEFAULT_PAGE_NUMBER;
          python_call("backend", null, pageSize, pageNumber).then(info => this.loadPage("videos", info)).catch(backend_error);
        }

        loadPropertiesPage() {
          python_call("describe_prop_types").then(definitions => this.loadPage("properties", {
            definitions: definitions
          })).catch(backend_error);
        }

      });
    }
  };
});