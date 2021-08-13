System.register(["../dialogs/Dialog.js", "../utils/backend.js"], function (_export, _context) {
  "use strict";

  var Dialog, backend_error, python_call, FormDatabaseFolders;

  _export("FormDatabaseFolders", void 0);

  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }],
    execute: function () {
      _export("FormDatabaseFolders", FormDatabaseFolders = class FormDatabaseFolders extends React.Component {
        constructor(props) {
          // database: {name: str, folders: [str]}
          // onClose(paths)
          super(props);
          this.state = {
            paths: new Set(this.props.database.folders)
          };
          this.onClose = this.onClose.bind(this);
          this.removePath = this.removePath.bind(this);
          this.addFolder = this.addFolder.bind(this);
          this.addFile = this.addFile.bind(this);
        }

        render() {
          const database = this.props.database;
          const paths = Array.from(this.state.paths);
          paths.sort();
          return /*#__PURE__*/React.createElement(Dialog, {
            title: `Edit ${paths.length} folders for database: ${database.name}`,
            yes: "save",
            action: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "path-edition vertical"
          }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            onClick: this.addFolder
          }, "Add folder")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            onClick: this.addFile
          }, "Add file")))), /*#__PURE__*/React.createElement("div", {
            className: "paths"
          }, /*#__PURE__*/React.createElement("table", null, paths.map((path, index) => /*#__PURE__*/React.createElement("tr", {
            key: index
          }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("code", null, path)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            onClick: () => this.removePath(path)
          }, "-"))))))));
        }

        removePath(path) {
          const paths = new Set(this.state.paths);
          paths.delete(path);
          this.setState({
            paths
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

        onClose() {
          this.props.onClose(Array.from(this.state.paths));
        }

      });

      FormDatabaseFolders.propTypes = {
        database: PropTypes.shape({
          name: PropTypes.string.isRequired,
          folders: PropTypes.arrayOf(PropTypes.string)
        }),
        onClose: PropTypes.func.isRequired
      };
    }
  };
});