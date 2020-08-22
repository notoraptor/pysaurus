System.register([], function (_export, _context) {
  "use strict";

  var Pagination;

  _export("Pagination", void 0);

  return {
    setters: [],
    execute: function () {
      _export("Pagination", Pagination = class Pagination extends React.Component {
        constructor(props) {
          // singular: str
          // plural: str
          // nbPages: int
          // pageNumber: int
          // onChange: function(int)
          super(props);
          this.onFirst = this.onFirst.bind(this);
          this.onNext = this.onNext.bind(this);
          this.onLast = this.onLast.bind(this);
          this.onPrevious = this.onPrevious.bind(this);
          this.onInput = this.onInput.bind(this);
        }

        render() {
          const singular = this.props.singular;
          const plural = this.props.plural;
          const nbPages = this.props.nbPages;
          const pageNumber = this.props.pageNumber;
          const nbCharacters = Math.round(Math.log10(nbPages)) + 1;
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
          }, "<"), ' ', /*#__PURE__*/React.createElement("span", null, Utils.sentence(singular), ' ', /*#__PURE__*/React.createElement("input", {
            type: "number",
            className: "current",
            size: nbCharacters,
            min: 1,
            max: nbPages,
            step: 1,
            value: pageNumber + 1,
            onChange: this.onInput
          }), " / ", nbPages), ' ', /*#__PURE__*/React.createElement("button", {
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

        onInput(event) {
          const value = event.target.value;
          let pageNumber = (value || 1) - 1;
          if (pageNumber >= this.props.nbPages) pageNumber = this.props.nbPages - 1;
          if (pageNumber < 0) pageNumber = 0;
          if (pageNumber !== this.props.pageNumber) this.props.onChange(pageNumber);
        }

      });
    }
  };
});