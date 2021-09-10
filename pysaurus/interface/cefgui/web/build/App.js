System.register(["./pages/Test.js", "./pages/HomePage.js", "./pages/VideosPage.js", "./pages/PropertiesPage.js", "./pages/DatabasesPage.js", "./utils/backend.js", "./utils/constants.js"], function (_export, _context) {
  "use strict";

  var Test, HomePage, VideosPage, PropertiesPage, DatabasesPage, backend_error, python_call, VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE, App;

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
            className: "flex-grow-1 vertical"
          }, /*#__PURE__*/React.createElement("main", {
            className: "flex-grow-1 vertical"
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
            python_call("list_databases").then(databases => this.dbHome(databases)).catch(backend_error);
          }
        }

        loadPage(pageName, parameters = undefined) {
          parameters = parameters ? parameters : {};
          this.setState({
            page: pageName,
            parameters: parameters
          });
        } // Public methods for children components.


        dbHome(databases = undefined) {
          this.loadPage("databases", databases === undefined ? databases : {
            databases
          });
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
          python_call('get_prop_types').then(definitions => this.loadPage("properties", {
            definitions: definitions
          })).catch(backend_error);
        }

      });
    }
  };
});