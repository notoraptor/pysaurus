System.register(["../BaseComponent.js", "../dialogs/FancyBox.js", "../language.js", "../utils/FancyboxManager.js"], function (_export, _context) {
  "use strict";

  var BaseComponent, FancyBox, tr, Fancybox, FormVideosSearch;
  _export("FormVideosSearch", void 0);
  return {
    setters: [function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }, function (_dialogsFancyBoxJs) {
      FancyBox = _dialogsFancyBoxJs.FancyBox;
    }, function (_languageJs) {
      tr = _languageJs.tr;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }],
    execute: function () {
      _export("FormVideosSearch", FormVideosSearch = class FormVideosSearch extends BaseComponent {
        // text
        // cond
        // onClose(criterion)

        getInitialState() {
          return {
            text: this.props.text || "",
            cond: this.props.cond || ""
          };
        }
        render() {
          return /*#__PURE__*/React.createElement(FancyBox, {
            title: tr("Search videos")
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-videos-search text-center"
          }, tr(`
Type text to search and choose how to search.

You can also type text and then press enter
to automatically select "AND" as search method.
`, null, "markdown"), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
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
            checked: this.state.cond === "and"
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-and"
          }, tr("all terms"))), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-or",
            name: "searchType",
            value: "or",
            onChange: this.onChangeCond,
            checked: this.state.cond === "or"
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-or"
          }, tr("any term"))), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-exact",
            name: "searchType",
            value: "exact",
            onChange: this.onChangeCond,
            checked: this.state.cond === "exact"
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-exact"
          }, tr("exact sentence"))), /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("input", {
            type: "radio",
            id: "input-search-id",
            name: "searchType",
            value: "id",
            onChange: this.onChangeCond,
            checked: this.state.cond === "id"
          }), /*#__PURE__*/React.createElement("label", {
            htmlFor: "input-search-id"
          }, tr("video ID")))));
        }
        componentDidMount() {
          document.querySelector("#input-search").focus();
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
              const cond = "and";
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