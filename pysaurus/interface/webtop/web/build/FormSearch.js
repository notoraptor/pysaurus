System.register([], function (_export, _context) {
  "use strict";

  var FormSearch;

  _export("FormSearch", void 0);

  return {
    setters: [],
    execute: function () {
      _export("FormSearch", FormSearch = class FormSearch extends React.Component {
        constructor(props) {
          // text
          // cond
          // onClose(criterion)
          super(props);
          this.state = {
            text: this.props.text || '',
            cond: this.props.cond || ''
          };
          this.onFocusInput = this.onFocusInput.bind(this);
          this.onChangeInput = this.onChangeInput.bind(this);
          this.onChangeCond = this.onChangeCond.bind(this);
          this.onInput = this.onInput.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("form", {
            className: "status form-search"
          }, /*#__PURE__*/React.createElement("p", null, "Type text to search and choose how to search."), /*#__PURE__*/React.createElement("p", null, "You can also type text and then press enter to automatically select \"AND\" as search method."), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "text",
            id: "input-search",
            name: "searchText",
            placeholder: "Search ...",
            onFocus: this.onFocusInput,
            onChange: this.onChangeInput,
            onKeyDown: this.onInput,
            value: this.state.text
          })), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-and",
            name: "searchType",
            value: "and",
            onChange: this.onChangeCond,
            checked: this.state.cond === 'and'
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-and"
          }, "all terms")), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-or",
            name: "searchType",
            value: "or",
            onChange: this.onChangeCond,
            checked: this.state.cond === 'or'
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-or"
          }, "any term")), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-exact",
            name: "searchType",
            value: "exact",
            onChange: this.onChangeCond,
            checked: this.state.cond === 'exact'
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-exact"
          }, "exact sentence")));
        }

        componentDidMount() {
          document.querySelector('#input-search').focus();
        }

        onFocusInput(event) {
          event.target.select();
        }

        onChangeInput(event) {
          this.setState({
            text: event.target.value,
            cond: ''
          });
        }

        onChangeCond(event) {
          const text = this.state.text;
          const cond = event.target.value;
          this.setState({
            text,
            cond
          }, () => {
            if (text.length && cond.length) this.props.onClose({
              text,
              cond
            });
          });
        }

        onInput(event) {
          if (event.key === "Enter") {
            if (this.state.text.length) {
              const text = this.state.text;
              const cond = 'and';
              this.props.onClose({
                text,
                cond
              });
              return true;
            }
          }
        }

      });
    }
  };
});