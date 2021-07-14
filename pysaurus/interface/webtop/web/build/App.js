System.register(["./pages/Test.js", "./pages/HomePage.js", "./pages/VideosPage.js", "./pages/PropertiesPage.js", "./utils/backend.js", "./pages/DatabasesPage.js", "./utils/constants.js"], function (_export, _context) {
  "use strict";

  var Test, HomePage, VideosPage, PropertiesPage, backend_error, python_call, DatabasesPage, VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE, App;

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
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_pagesDatabasesPageJs) {
      DatabasesPage = _pagesDatabasesPageJs.DatabasesPage;
    }, function (_utilsConstantsJs) {
      VIDEO_DEFAULT_PAGE_NUMBER = _utilsConstantsJs.VIDEO_DEFAULT_PAGE_NUMBER;
      VIDEO_DEFAULT_PAGE_SIZE = _utilsConstantsJs.VIDEO_DEFAULT_PAGE_SIZE;
    }],
    execute: function () {
      _export("App", App = class App extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            page: null,
            parameters: {}
          };
          this.loadPage = this.loadPage.bind(this);
          this.loadPropertiesPage = this.loadPropertiesPage.bind(this);
          this.loadVideosPage = this.loadVideosPage.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "app vertical"
          }, /*#__PURE__*/React.createElement("main", {
            className: "vertical"
          }, this.renderPage()));
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
            python_call("list_databases").then(databases => {
              this.loadPage("databases", {
                databases
              });
            }).catch(backend_error);
          }
        }

        loadPage(pageName, parameters = undefined) {
          parameters = parameters ? parameters : {};
          this.setState({
            page: pageName,
            parameters: parameters
          });
        } // Public methods for children components.


        dbHome() {
          this.loadPage("databases");
        }

        dbLoad() {
          this.loadPage("home");
        }

        dbUpdate() {
          this.loadPage("home", {
            action: "update"
          });
        }

        dbFindSimilarities() {
          this.loadPage("home", {
            action: "similarities"
          });
        }

        dbFindSimilaritiesIgnoreCache() {
          this.loadPage("home", {
            action: "similaritiesNoCache"
          });
        }

        loadVideosPage(pageSize = undefined, pageNumber = undefined) {
          if (pageSize === undefined) pageSize = VIDEO_DEFAULT_PAGE_SIZE;
          if (pageNumber === undefined) pageNumber = VIDEO_DEFAULT_PAGE_NUMBER;
          python_call("backend", null, pageSize, pageNumber).then(info => this.loadPage("videos", info)).catch(backend_error);
        }

        loadPropertiesPage() {
          python_call('get_prop_types').then(definitions => this.loadPage("properties", {
            definitions: definitions
          })).catch(backend_error);
        }

      });
    }
  };
});