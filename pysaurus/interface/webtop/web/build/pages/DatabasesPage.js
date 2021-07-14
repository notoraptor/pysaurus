System.register(["../utils/backend.js"], function (_export, _context) {
  "use strict";

  var backend_error, python_call, DatabasesPage;

  _export("DatabasesPage", void 0);

  return {
    setters: [function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }],
    execute: function () {
      _export("DatabasesPage", DatabasesPage = class DatabasesPage extends React.Component {
        constructor(props) {
          // parameters: {databases: [{name, path}]}
          // app: App
          super(props);
          this.state = {
            name: "",
            paths: new Set(),
            update: true
          };
          this.onChangeName = this.onChangeName.bind(this);
          this.addFolder = this.addFolder.bind(this);
          this.addFile = this.addFile.bind(this);
          this.removePath = this.removePath.bind(this);
          this.createDatabase = this.createDatabase.bind(this);
          this.openDatabase = this.openDatabase.bind(this);
          this.onChangeUpdate = this.onChangeUpdate.bind(this);
        }

        render() {
          const paths = Array.from(this.state.paths);
          paths.sort();
          return /*#__PURE__*/React.createElement("div", {
            id: "databases"
          }, /*#__PURE__*/React.createElement("h1", null, "Welcome to ", window.PYTHON_APP_NAME), /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("h2", null, "Create a new database"), /*#__PURE__*/React.createElement("div", {
            className: "padding"
          }, /*#__PURE__*/React.createElement("input", {
            type: "text",
            value: this.state.name,
            onChange: this.onChangeName,
            placeholder: "Database name."
          })), /*#__PURE__*/React.createElement("h3", null, "Database folders and files"), /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            onClick: this.addFolder
          }, "Add folder"), " "), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            onClick: this.addFile
          }, "Add file")))), /*#__PURE__*/React.createElement("table", null, paths.map((path, index) => /*#__PURE__*/React.createElement("tr", {
            key: index
          }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("code", null, path)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            onClick: () => this.removePath(path)
          }, "-"))))), /*#__PURE__*/React.createElement("div", {
            className: "padding"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: this.createDatabase
          }, "create database"))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("h2", null, "Open an existing database"), /*#__PURE__*/React.createElement("div", {
            className: "padding"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "update",
            checked: this.state.update,
            onChange: this.onChangeUpdate
          }), " ", /*#__PURE__*/React.createElement("label", {
            htmlFor: "update"
          }, "update after opening")), /*#__PURE__*/React.createElement("h3", null, "Click on a database to open it"), this.props.parameters.databases.map((database, index) => /*#__PURE__*/React.createElement("div", {
            className: "padding",
            key: index
          }, /*#__PURE__*/React.createElement("button", {
            onClick: () => this.openDatabase(database.path)
          }, database.name)))))));
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

        addFolder() {
          python_call("select_directory").then(directory => {
            if (directory) {
              const paths = new Set(this.state.paths);
              paths.add(directory);
              this.setState({
                paths
              });
            }
          }).catch(backend_error);
        }

        addFile() {
          python_call("select_file").then(file => {
            if (file) {
              const paths = new Set(this.state.paths);
              paths.add(file);
              this.setState({
                paths
              });
            }
          }).catch(backend_error);
        }

        removePath(path) {
          const paths = new Set(this.state.paths);
          paths.delete(path);
          this.setState({
            paths
          });
        }

        createDatabase() {
          python_call("create_database", this.state.name, Array.from(this.state.paths), this.state.update).then(() => this.props.app.dbUpdate()).catch(backend_error);
        }

        openDatabase(path) {
          python_call("open_database", path, this.state.update).then(() => this.props.app.dbUpdate()).catch(backend_error);
        }

      });
    }
  };
});