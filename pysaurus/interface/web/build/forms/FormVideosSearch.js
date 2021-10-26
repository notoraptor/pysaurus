System.register(["../dialogs/FancyBox.js"], function (_export, _context) {
  "use strict";

  var FancyBox, FormVideosSearch;

  _export("FormVideosSearch", void 0);

  return {
    setters: [function (_dialogsFancyBoxJs) {
      FancyBox = _dialogsFancyBoxJs.FancyBox;
    }],
    execute: function () {
      _export("FormVideosSearch", FormVideosSearch = class FormVideosSearch extends React.Component {
        constructor(props) {
          // text
          // cond
          // onClose(criterion)
          super(props);
          this.state = {
            text: this.props.text || "",
            cond: this.props.cond || ""
          };
          this.onFocusInput = this.onFocusInput.bind(this);
          this.onChangeInput = this.onChangeInput.bind(this);
          this.onChangeCond = this.onChangeCond.bind(this);
          this.onInput = this.onInput.bind(this);
          this.onClose = this.onClose.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(FancyBox, {
            title: PYTHON_LANG.form_title_search_videos
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-videos-search text-center"
          }, markdownToReact(PYTHON_LANG.form_content_search_videos), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "text",
            id: "input-search",
            className: "block mb-2",
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
          }, PYTHON_LANG.search_and)), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-or",
            name: "searchType",
            value: "or",
            onChange: this.onChangeCond,
            checked: this.state.cond === 'or'
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-or"
          }, PYTHON_LANG.search_or)), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-exact",
            name: "searchType",
            value: "exact",
            onChange: this.onChangeCond,
            checked: this.state.cond === 'exact'
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-exact"
          }, PYTHON_LANG.search_exact_sentence)), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-id",
            name: "searchType",
            value: "id",
            onChange: this.onChangeCond,
            checked: this.state.cond === 'id'
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-id"
          }, PYTHON_LANG.search_id))));
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
            cond: ""
          });
        }

        onChangeCond(event) {
          const text = this.state.text;
          const cond = event.target.value;
          this.setState({
            text,
            cond
          }, () => {
            if (text.length && cond.length) this.onClose({
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
              this.onClose({
                text,
                cond
              });
              return true;
            }
          }
        }

        onClose(criterion) {
          Fancybox.close();
          this.props.onClose(criterion);
        }

      });
    }
  };
});