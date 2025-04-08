System.register(["../language.js", "../utils/backend.js", "../BaseComponent.js"], function (_export, _context) {
  "use strict";

  var tr, backend_error, python_call, BaseComponent, PathsInput;
  _export("PathsInput", void 0);
  return {
    setters: [function (_languageJs) {
      tr = _languageJs.tr;
    }, function (_utilsBackendJs) {
      backend_error = _utilsBackendJs.backend_error;
      python_call = _utilsBackendJs.python_call;
    }, function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }],
    execute: function () {
      _export("PathsInput", PathsInput = class PathsInput extends BaseComponent {
        render() {
          const paths = this.props.data || [];
          return /*#__PURE__*/React.createElement("div", {
            className: "form-database-edit-folders flex-grow-1 position-relative"
          }, /*#__PURE__*/React.createElement("div", {
            className: "absolute-plain vertical"
          }, /*#__PURE__*/React.createElement("table", {
            className: "table-layout-fixed flex-shrink-0"
          }, /*#__PURE__*/React.createElement("tbody", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.addFolder
          }, tr("Add folder"))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: this.addFile
          }, tr("Add file")))))), /*#__PURE__*/React.createElement("div", {
            className: "paths flex-grow-1 overflow-auto"
          }, /*#__PURE__*/React.createElement("table", {
            className: "table-layout-fixed"
          }, /*#__PURE__*/React.createElement("tbody", null, paths.map((path, index) => /*#__PURE__*/React.createElement("tr", {
            key: index
          }, /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("code", null, path)), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "block",
            onClick: () => this.removePath(path)
          }, "-")))))))));
        }
        addFolder() {
          python_call("select_directory").then(this._extendPaths).catch(backend_error);
        }
        addFile() {
          python_call("select_file").then(this._extendPaths).catch(backend_error);
        }
        _extendPaths(path) {
          if (path) {
            const paths = new Set(this.props.data || []);
            paths.add(path);
            const data = Array.from(paths);
            data.sort();
            this.props.onUpdate(data);
          }
        }
        removePath(path) {
          const paths = new Set(this.props.data || []);
          paths.delete(path);
          const data = Array.from(paths);
          data.sort();
          this.props.onUpdate(data);
        }
      });
      PathsInput.propTypes = {
        data: PropTypes.arrayOf(PropTypes.string),
        // onUpdate(arr)
        onUpdate: PropTypes.func.isRequired
      };
    }
  };
});