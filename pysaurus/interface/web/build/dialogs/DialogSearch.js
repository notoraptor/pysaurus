System.register(["../components/Cell.js", "./Dialog.js"], function (_export, _context) {
  "use strict";

  var Cell, Dialog, DialogSearch;

  _export("DialogSearch", void 0);

  return {
    setters: [function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }, function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }],
    execute: function () {
      _export("DialogSearch", DialogSearch = class DialogSearch extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            text: ""
          };
          this.onFocusInput = this.onFocusInput.bind(this);
          this.onChangeInput = this.onChangeInput.bind(this);
          this.onInput = this.onInput.bind(this);
          this.onClose = this.onClose.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            title: this.props.title,
            yes: "go",
            action: this.onClose
          }, /*#__PURE__*/React.createElement(Cell, {
            center: true,
            full: true,
            className: "text-center"
          }, /*#__PURE__*/React.createElement("input", {
            type: "text",
            id: "input-search",
            placeholder: "Search ...",
            onFocus: this.onFocusInput,
            onChange: this.onChangeInput,
            onKeyDown: this.onInput,
            value: this.state.text
          })));
        }

        componentDidMount() {
          document.querySelector('#input-search').focus();
        }

        onFocusInput(event) {
          event.target.select();
        }

        onChangeInput(event) {
          this.setState({
            text: event.target.value
          });
        }

        onInput(event) {
          if (event.key === "Enter" && this.state.text) {
            Fancybox.close();
            this.props.onSearch(this.state.text);
            return true;
          }
        }

        onClose() {
          if (this.state.text) this.props.onSearch(this.state.text);
        }

      });

      DialogSearch.propTypes = {
        title: PropTypes.string.isRequired,
        // onSearch(str)
        onSearch: PropTypes.func.isRequired
      };
    }
  };
});