System.register(["../BaseComponent.js", "../dialogs/DialogSearch.js", "../forms/FormPaginationGoTo.js", "../utils/FancyboxManager.js", "../utils/functions.js"], function (_export, _context) {
  "use strict";

  var BaseComponent, DialogSearch, FormPaginationGoTo, Fancybox, capitalizeFirstLetter, Pagination;
  _export("Pagination", void 0);
  return {
    setters: [function (_BaseComponentJs) {
      BaseComponent = _BaseComponentJs.BaseComponent;
    }, function (_dialogsDialogSearchJs) {
      DialogSearch = _dialogsDialogSearchJs.DialogSearch;
    }, function (_formsFormPaginationGoToJs) {
      FormPaginationGoTo = _formsFormPaginationGoToJs.FormPaginationGoTo;
    }, function (_utilsFancyboxManagerJs) {
      Fancybox = _utilsFancyboxManagerJs.Fancybox;
    }, function (_utilsFunctionsJs) {
      capitalizeFirstLetter = _utilsFunctionsJs.capitalizeFirstLetter;
    }],
    execute: function () {
      _export("Pagination", Pagination = class Pagination extends BaseComponent {
        // singular: str
        // plural: str
        // nbPages: int
        // pageNumber: int
        // onChange: function(int)
        // onSearch? function(str)

        render() {
          const singular = this.props.singular;
          const plural = this.props.plural;
          const nbPages = this.props.nbPages;
          const pageNumber = this.props.pageNumber;
          return nbPages ? /*#__PURE__*/React.createElement("span", {
            className: "navigation py-1 text-center"
          }, /*#__PURE__*/React.createElement("button", {
            className: "first",
            disabled: pageNumber === 0,
            onClick: this.onFirst
          }, "<<"), /*#__PURE__*/React.createElement("button", {
            className: "previous",
            disabled: pageNumber === 0,
            onClick: this.onPrevious
          }, "<"), /*#__PURE__*/React.createElement("span", this.props.onSearch ? {
            className: "go",
            onClick: this.look
          } : {}, capitalizeFirstLetter(singular)), /*#__PURE__*/React.createElement("span", {
            className: "go clickable",
            onClick: this.go
          }, pageNumber + 1, "/", nbPages), /*#__PURE__*/React.createElement("button", {
            className: "next",
            disabled: pageNumber === nbPages - 1,
            onClick: this.onNext
          }, ">"), /*#__PURE__*/React.createElement("button", {
            className: "last",
            disabled: pageNumber === nbPages - 1,
            onClick: this.onLast
          }, ">>")) : /*#__PURE__*/React.createElement("span", {
            className: "navigation py-1 text-center"
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
          Fancybox.load(/*#__PURE__*/React.createElement(FormPaginationGoTo, {
            nbPages: this.props.nbPages,
            pageNumber: this.props.pageNumber,
            onClose: pageNumber => {
              if (pageNumber !== this.props.pageNumber) this.props.onChange(pageNumber);
            }
          }));
        }
        look() {
          Fancybox.load(/*#__PURE__*/React.createElement(DialogSearch, {
            title: "Search first:",
            onSearch: this.props.onSearch
          }));
        }
      });
    }
  };
});