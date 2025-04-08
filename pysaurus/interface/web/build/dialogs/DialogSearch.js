System.register(["../components/Cell.js", "../utils/FancyboxManager.js", "./Dialog.js", "../BaseComponent.js"], function (_export, _context) {
  "use strict";

  var Cell, Fancybox, Dialog, BaseComponent, DialogSearch;
  _export("DialogSearch", void 0);
  return {
    setters: [function (_componentsCellJs) {
      Cell = _componentsCellJs.Cell;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }, function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }, function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }],
    execute: function () {
      _export("DialogSearch", DialogSearch = class DialogSearch extends BaseComponent {
        getInitialState() {
          return {
            text: ""
          };
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
          document.querySelector("#input-search").focus();
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