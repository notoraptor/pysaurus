System.register(["../forms/FormGoToPage.js", "../dialogs/DialogSearch.js"], function (_export, _context) {
  "use strict";

  var FormGoToPage, DialogSearch, Pagination;

  _export("Pagination", void 0);

  return {
    setters: [function (_formsFormGoToPageJs) {
      FormGoToPage = _formsFormGoToPageJs.FormGoToPage;
    }, function (_dialogsDialogSearchJs) {
      DialogSearch = _dialogsDialogSearchJs.DialogSearch;
    }],
    execute: function () {
      _export("Pagination", Pagination = class Pagination extends React.Component {
        constructor(props) {
          // singular: str
          // plural: str
          // nbPages: int
          // pageNumber: int
          // onChange: function(int)
          // onSearch? function(str)
          super(props);
          this.onFirst = this.onFirst.bind(this);
          this.onNext = this.onNext.bind(this);
          this.onLast = this.onLast.bind(this);
          this.onPrevious = this.onPrevious.bind(this);
          this.go = this.go.bind(this);
          this.look = this.look.bind(this);
        }

        render() {
          const singular = this.props.singular;
          const plural = this.props.plural;
          const nbPages = this.props.nbPages;
          const pageNumber = this.props.pageNumber;
          return nbPages ? /*#__PURE__*/React.createElement("span", {
            className: "navigation"
          }, /*#__PURE__*/React.createElement("button", {
            className: "first",
            disabled: pageNumber === 0,
            onClick: this.onFirst
          }, "<<"), /*#__PURE__*/React.createElement("button", {
            className: "previous",
            disabled: pageNumber === 0,
            onClick: this.onPrevious
          }, "<"), /*#__PURE__*/React.createElement("span", {
            className: "go",
            onClick: this.props.onSearch ? this.look : this.look
          }, Utils.sentence(singular)), /*#__PURE__*/React.createElement("span", {
            className: "go",
            onClick: this.go
          }, pageNumber + 1, "/", nbPages), /*#__PURE__*/React.createElement("button", {
            className: "next",
            disabled: pageNumber === nbPages - 1,
            onClick: this.onNext
          }, ">"), /*#__PURE__*/React.createElement("button", {
            className: "last",
            disabled: pageNumber === nbPages - 1,
            onClick: this.onLast
          }, ">>")) : /*#__PURE__*/React.createElement("div", {
            className: "navigation status"
          }, /*#__PURE__*/React.createElement("em", null, "0 ", plural));
        }

        onFirst() {
          if (this.props.pageNumber !== 0) {
            this.props.onChange(0);
          }
        }

        onPrevious() {
          if (this.props.pageNumber > 0) {
            this.props.onChange(this.props.pageNumber - 1);
          }
        }

        onNext() {
          if (this.props.pageNumber < this.props.nbPages - 1) {
            this.props.onChange(this.props.pageNumber + 1);
          }
        }

        onLast() {
          if (this.props.pageNumber !== this.props.nbPages - 1) {
            this.props.onChange(this.props.nbPages - 1);
          }
        }

        go() {
          APP.loadDialog('Go to page:', onClose => /*#__PURE__*/React.createElement(FormGoToPage, {
            nbPages: this.props.nbPages,
            pageNumber: this.props.pageNumber,
            onClose: pageNumber => {
              onClose();
              if (pageNumber !== this.props.pageNumber) this.props.onChange(pageNumber);
            }
          }));
        }

        look() {
          APP.loadDialog('Search first:', onClose => /*#__PURE__*/React.createElement(DialogSearch, {
            onClose: text => {
              onClose();
              if (text && text.length) this.props.onSearch(text);
            }
          }));
        }

      });
    }
  };
});