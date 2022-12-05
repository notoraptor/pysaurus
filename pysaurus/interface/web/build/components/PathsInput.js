System.register(["../language.js", "../utils/backend.js"], function (_export, _context) {
  "use strict";

  var LangContext, tr, backend_error, python_call, PathsInput;

  _export("PathsInput", void 0);

  return {
    setters: [function (_languageJs) {
      LangContext = _languageJs.LangContext;
      tr = _languageJs.tr;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }],
    execute: function () {
      _export("PathsInput", PathsInput = class PathsInput extends React.Component {
        constructor(props) {
          super(props);
          this.addFolder = this.addFolder.bind(this);
          this.addFile = this.addFile.bind(this);
          this.removePath = this.removePath.bind(this);
        }

        render() {
          const paths = this.props.data || [];
          return /*#__PURE__*/React.createElement("div", {
            className: "form-database-edit-folders flex-grow-1 position-relative"
          }, /*#__PURE__*/React.createElement("div", {
            className: "absolute-plain vertical"
          }, /*#__PURE__*/React.createElement("table", {
            className: "table-layout-fixed flex-shrink-0"
          }, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.addFolder
          }, tr("Add folder"))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.addFile
          }, tr("Add file"))))), /*#__PURE__*/React.createElement("div", {
            className: "paths flex-grow-1 overflow-auto"
          }, /*#__PURE__*/React.createElement("table", {
            className: "table-layout-fixed"
          }, paths.map((path, index) => /*#__PURE__*/React.createElement("tr", {
            key: index
          }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("code", null, path)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: () => this.removePath(path)
          }, "-"))))))));
        }

        addFolder() {
          python_call("select_directory").then(directory => {
            if (directory) {
              const paths = new Set(this.props.data || []);
              paths.add(directory);
              const data = Array.from(paths);
              data.sort();
              this.props.onUpdate(data);
            }
          }).catch(backend_error);
        }

        addFile() {
          python_call("select_file").then(file => {
            if (file) {
              const paths = new Set(this.props.data || []);
              paths.add(file);
              const data = Array.from(paths);
              data.sort();
              this.props.onUpdate(data);
            }
          }).catch(backend_error);
        }

        removePath(path) {
          const paths = new Set(this.props.data || []);
          paths.delete(path);
          const data = Array.from(paths);
          data.sort();
          this.props.onUpdate(data);
        }

      });

      PathsInput.contextType = LangContext;
      PathsInput.propTypes = {
        data: PropTypes.arrayOf(PropTypes.string),
        // onUpdate(arr)
        onUpdate: PropTypes.func.isRequired
      };
    }
  };
});