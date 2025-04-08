System.register(["./pages/DatabasesPage.js", "./pages/HomePage.js", "./pages/PropertiesPage.js", "./pages/Test.js", "./pages/VideosPage.js", "./utils/backend.js", "./utils/constants.js", "./utils/globals.js", "./BaseComponent.js"], function (_export, _context) {
  "use strict";

  var DatabasesPage, HomePage, PropertiesPage, Test, VideosPage, backend_error, python_call, python_multiple_call, VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE, APP_STATE, BaseComponent, App;
  _export("App", void 0);
  return {
    setters: [function (_pagesDatabasesPageJs) {
      DatabasesPage = _pagesDatabasesPageJs.DatabasesPage;
    }, function (_pagesHomePageJs) {
      HomePage = _pagesHomePageJs.HomePage;
    }, function (_pagesPropertiesPageJs) {
      PropertiesPage = _pagesPropertiesPageJs.PropertiesPage;
    }, function (_pagesTestJs) {
      Test = _pagesTestJs.Test;
    }, function (_pagesVideosPageJs) {
      VideosPage = _pagesVideosPageJs.VideosPage;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
      python_multiple_call = _utilsBackendJs.python_multiple_call;
    }, function (_utilsConstantsJs) {
      VIDEO_DEFAULT_PAGE_NUMBER = _utilsConstantsJs.VIDEO_DEFAULT_PAGE_NUMBER;
      VIDEO_DEFAULT_PAGE_SIZE = _utilsConstantsJs.VIDEO_DEFAULT_PAGE_SIZE;
    }, function (_utilsGlobalsJs) {
      APP_STATE = _utilsGlobalsJs.APP_STATE;
    }, function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }],
    execute: function () {
      _export("App", App = class App extends BaseComponent {
        constructor(props) {
          super(props);
          APP_STATE.lang = this.state.lang;
        }
        getInitialState() {
          return {
            page: null,
            parameters: {},
            lang: window.PYTHON_LANG,
            languages: []
          };
        }
        render() {
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
            python_multiple_call(["get_language_names"], ["get_database_names"]).then(([language_names, database_names]) => this.dbHome({
              language_names,
              database_names
            })).catch(backend_error);
          }
        }
        loadPage(pageName, parameters = undefined, otherState = undefined) {
          this.setState(Object.assign({}, otherState || {}, {
            page: pageName,
            parameters: parameters || {}
          }));
        }

        // Public methods for children components.

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
          const localState = {};
          if (appState.language_names) {
            localState.languages = appState.language_names;
          } else {
            appState.language_names = this.getLanguages();
          }
          this.loadPage("databases", appState, localState);
        }
        dbUpdate(...command) {
          this.loadPage("home", {
            command
          });
        }
        loadVideosPage(pageSize = undefined, pageNumber = undefined) {
          if (pageSize === undefined) pageSize = VIDEO_DEFAULT_PAGE_SIZE;
          if (pageNumber === undefined) pageNumber = VIDEO_DEFAULT_PAGE_NUMBER;
          python_call("backend", pageSize, pageNumber).then(info => this.loadPage("videos", info)).catch(backend_error);
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