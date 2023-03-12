System.register(["../utils/backend.js", "../components/PathsInput.js", "../language.js"], function (_export, _context) {
  "use strict";

  var backend_error, python_call, PathsInput, LangContext, tr, DatabasesPage;

  _export("DatabasesPage", void 0);

  return {
    setters: [function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_componentsPathsInputJs) {
      PathsInput = _componentsPathsInputJs.PathsInput;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
      tr = _languageJs.tr;
    }],
    execute: function () {
      _export("DatabasesPage", DatabasesPage = class DatabasesPage extends React.Component {
        constructor(props) {
          // parameters: {databases: [name: str], languages: [name: str]}
          // app: App
          super(props);
          this.state = {
            name: "",
            paths: [],
            update: true
          };
          this.onChangeName = this.onChangeName.bind(this);
          this.createDatabase = this.createDatabase.bind(this);
          this.openDatabase = this.openDatabase.bind(this);
          this.onChangeUpdate = this.onChangeUpdate.bind(this);
          this.onChangeLanguage = this.onChangeLanguage.bind(this);
          this.onUpdatePaths = this.onUpdatePaths.bind(this);
        }

        render() {
          const languages = this.props.parameters.language_names;
          const paths = Array.from(this.state.paths);
          paths.sort();
          return /*#__PURE__*/React.createElement("div", {
            id: "databases",
            className: "text-center"
          }, /*#__PURE__*/React.createElement("h1", null, tr("Welcome to {name}", {
            name: window.PYTHON_APP_NAME
          })), /*#__PURE__*/React.createElement("table", {
            className: "w-100 table-layout-fixed"
          }, languages.length > 1 ? /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
            className: "text-right"
          }, /*#__PURE__*/React.createElement("label", {
            htmlFor: "language"
          }, tr("Language:"), ":")), /*#__PURE__*/React.createElement("td", {
            className: "text-left"
          }, /*#__PURE__*/React.createElement("select", {
            id: "language",
            value: window.PYTHON_LANGUAGE,
            onChange: this.onChangeLanguage
          }, languages.map((language, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: language
          }, language))))) : "", /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("h2", null, tr("Create a database")), /*#__PURE__*/React.createElement("div", {
            className: "p-1"
          }, /*#__PURE__*/React.createElement("input", {
            type: "text",
            className: "w-100",
            value: this.state.name,
            onChange: this.onChangeName,
            placeholder: tr("Database name.")
          })), /*#__PURE__*/React.createElement("h3", null, tr("Database folders and files")), /*#__PURE__*/React.createElement("div", {
            className: "vertical new-paths"
          }, /*#__PURE__*/React.createElement(PathsInput, {
            onUpdate: this.onUpdatePaths,
            data: this.state.paths
          })), /*#__PURE__*/React.createElement("div", {
            className: "p-1"
          }, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.createDatabase
          }, tr("create database")))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("h2", null, tr("Open a database ({count} available)", {
            count: this.props.parameters.database_names.length
          })), /*#__PURE__*/React.createElement("div", {
            className: "p-1"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "update",
            checked: this.state.update,
            onChange: this.onChangeUpdate
          }), " ", /*#__PURE__*/React.createElement("label", {
            htmlFor: "update"
          }, tr("update after opening"))), /*#__PURE__*/React.createElement("h3", null, tr("Click on a database to open it")), this.props.parameters.database_names.map((database, index) => /*#__PURE__*/React.createElement("div", {
            className: "p-1",
            key: index
          }, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: () => this.openDatabase(database)
          }, database)))))));
        }

        onChangeLanguage(event) {
          this.props.app.setLanguage(event.target.value);
        }

        onChangeName(event) {
          const name = event.target.value;

          if (this.state.name !== name) {
            this.setState({
              name
            });
          }
        }

        onChangeUpdate(event) {
          this.setState({
            update: event.target.checked
          });
        }

        createDatabase() {
          // TODO: flag `update` should be either reserved to update_database, or display as global flag into this page
          this.props.app.dbUpdate("create_database", this.state.name, Array.from(this.state.paths), this.state.update);
        }

        openDatabase(name) {
          this.props.app.dbUpdate("open_database", name, this.state.update);
        }

        onUpdatePaths(paths) {
          this.setState({
            paths
          });
        }

      });

      DatabasesPage.contextType = LangContext;
    }
  };
});