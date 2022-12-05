System.register(["../dialogs/Dialog.js", "../language.js", "../components/PathsInput.js"], function (_export, _context) {
  "use strict";

  var Dialog, LangContext, tr, PathsInput, FormDatabaseEditFolders;

  _export("FormDatabaseEditFolders", void 0);

  return {
    setters: [function (_dialogsDialogJs) {
      Dialog = _dialogsDialogJs.Dialog;
    }, function (_languageJs) {
      LangContext = _languageJs.LangContext;
      tr = _languageJs.tr;
    }, function (_componentsPathsInputJs) {
      PathsInput = _componentsPathsInputJs.PathsInput;
    }],
    execute: function () {
      _export("FormDatabaseEditFolders", FormDatabaseEditFolders = class FormDatabaseEditFolders extends React.Component {
        constructor(props) {
          // database: {name: str, folders: [str]}
          // onClose(paths)
          super(props);
          this.state = {
            paths: this.props.database.folders.slice()
          };
          this.onUpdate = this.onUpdate.bind(this);
          this.onClose = this.onClose.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            title: tr("Edit {count} folders for database: {name}", {
              count: this.state.paths.length,
              name: this.props.database.name
            }),
            yes: tr("save"),
            action: this.onClose
          }, /*#__PURE__*/React.createElement(PathsInput, {
            onUpdate: this.onUpdate,
            data: this.state.paths
          }));
        }

        onUpdate(paths) {
          this.setState({
            paths
          });
        }

        onClose() {
          this.props.onClose(this.state.paths);
        }

      });

      FormDatabaseEditFolders.contextType = LangContext;
      FormDatabaseEditFolders.propTypes = {
        database: PropTypes.shape({
          name: PropTypes.string.isRequired,
          folders: PropTypes.arrayOf(PropTypes.string)
        }),
        onClose: PropTypes.func.isRequired
      };
    }
  };
});