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
            id: "databases",
            className: "text-center"
          }, /*#__PURE__*/React.createElement("h1", null, PYTHON_LANG.gui_database_welcome.format({
            name: window.PYTHON_APP_NAME
          })), /*#__PURE__*/React.createElement("table", {
            className: "w-100 table-layout-fixed"
          }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("h2", null, PYTHON_LANG.gui_database_create), /*#__PURE__*/React.createElement("div", {
            className: "p-1"
          }, /*#__PURE__*/React.createElement("input", {
            type: "text",
            className: "w-100",
            value: this.state.name,
            onChange: this.onChangeName,
            placeholder: PYTHON_LANG.gui_database_name_placeholder
          })), /*#__PURE__*/React.createElement("h3", null, PYTHON_LANG.gui_database_paths), /*#__PURE__*/React.createElement("table", {
            className: "w-100 table-layout-fixed"
          }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.addFolder
          }, PYTHON_LANG.gui_database_add_folder)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.addFile
          }, PYTHON_LANG.gui_database_add_file)))), /*#__PURE__*/React.createElement("table", {
            className: "w-100 table-layout-fixed"
          }, paths.map((path, index) => /*#__PURE__*/React.createElement("tr", {
            key: index
          }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("code", null, path)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: () => this.removePath(path)
          }, "-"))))), /*#__PURE__*/React.createElement("div", {
            className: "p-1"
          }, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.createDatabase
          }, PYTHON_LANG.gui_database_button_create))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("h2", null, PYTHON_LANG.gui_database_open.format({
            count: this.props.parameters.databases.length
          })), /*#__PURE__*/React.createElement("div", {
            className: "p-1"
          }, /*#__PURE__*/React.createElement("input", {
            type: "checkbox",
            id: "update",
            checked: this.state.update,
            onChange: this.onChangeUpdate
          }), " ", /*#__PURE__*/React.createElement("label", {
            htmlFor: "update"
          }, PYTHON_LANG.gui_database_update_after_opening)), /*#__PURE__*/React.createElement("h3", null, PYTHON_LANG.gui_database_click_to_open), this.props.parameters.databases.map((database, index) => /*#__PURE__*/React.createElement("div", {
            className: "p-1",
            key: index
          }, /*#__PURE__*/React.createElement("button", {
            className: "block",
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
          this.props.app.dbUpdate("create_database", this.state.name, Array.from(this.state.paths), this.state.update);
        }

        openDatabase(path) {
          this.props.app.dbUpdate("open_database", path, this.state.update);
        }

      });
    }
  };
});