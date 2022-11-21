System.register(["../language.js", "../utils/functions.js"], function (_export, _context) {
  "use strict";

  var LangContext, utilities, SetController, ComponentController, ComponentPropController, SetInput;

  function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

  _export({
    ComponentController: void 0,
    ComponentPropController: void 0,
    SetInput: void 0
  });

  return {
    setters: [function (_languageJs) {
      LangContext = _languageJs.LangContext;
    }, function (_utilsFunctionsJs) {
      utilities = _utilsFunctionsJs.utilities;
    }],
    execute: function () {
      SetController = class SetController {
        constructor() {//
        }

        size() {
          return 0;
        }

        get(index) {
          return null;
        }

        has(value) {
          return false;
        }

        add(value) {//
        }

        remove(value) {//
        }

      };

      _export("ComponentController", ComponentController = class ComponentController extends SetController {
        constructor(app, field, parser = null) {
          super();
          this.app = app;
          this.field = field;
          this.parser = parser;
        }

        size() {
          return this.app.state[this.field].length;
        }

        get(index) {
          return this.app.state[this.field][index];
        }

        has(value) {
          if (this.parser) value = this.parser(value);
          return this.app.state[this.field].indexOf(value) >= 0;
        }

        add(value) {
          const arr = this.app.state[this.field].slice();
          if (this.parser) value = this.parser(value);
          arr.push(value);
          this.app.setState({
            [this.field]: arr
          });
        }

        remove(toRemove) {
          if (this.parser) toRemove = this.parser(toRemove);
          const arr = [];

          for (let value of this.app.state[this.field]) {
            if (value !== toRemove) arr.push(value);
          }

          this.app.setState({
            [this.field]: arr
          });
        }

      });

      _export("ComponentPropController", ComponentPropController = class ComponentPropController extends ComponentController {
        constructor(app, field, propType, propEnum) {
          super(app, field, value => utilities(app.context).parsePropValString(propType, propEnum, value));
        }

      });

      _export("SetInput", SetInput = class SetInput extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            add: this.props.values ? this.props.values[0] : ""
          };
          this.onChangeAdd = this.onChangeAdd.bind(this);
          this.onInputAdd = this.onInputAdd.bind(this);
          this.onAdd = this.onAdd.bind(this);
          this.add = this.add.bind(this);
          this.remove = this.remove.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: `set-input ${this.props.className || ""}`
          }, /*#__PURE__*/React.createElement("table", {
            className: "first-td-text-right"
          }, /*#__PURE__*/React.createElement("tbody", null, this.renderList(), /*#__PURE__*/React.createElement("tr", {
            className: "form"
          }, /*#__PURE__*/React.createElement("td", null, this.props.values ? /*#__PURE__*/React.createElement("select", {
            value: this.state.add,
            onChange: this.onChangeAdd
          }, this.props.values.map((value, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: value
          }, value))) : /*#__PURE__*/React.createElement("input", _extends({
            type: "text",
            value: this.state.add,
            onChange: this.onChangeAdd,
            onKeyDown: this.onInputAdd,
            size: "10"
          }, this.props.identifier ? {
            id: this.props.identifier
          } : {}))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
            className: "add block",
            onClick: this.onAdd
          }, "+"))))));
        }

        renderList() {
          const output = [];
          const controller = this.props.controller;
          const size = controller.size();

          for (let i = 0; i < size; ++i) {
            const value = controller.get(i);
            output.push( /*#__PURE__*/React.createElement("tr", {
              className: "item",
              key: i
            }, /*#__PURE__*/React.createElement("td", null, value.toString()), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("button", {
              className: "remove block",
              onClick: () => this.remove(value)
            }, "-"))));
          }

          return output;
        }

        onChangeAdd(event) {
          this.setState({
            add: event.target.value
          });
        }

        onInputAdd(event) {
          if (event.key === "Enter") {
            this.add(this.state.add);
          }
        }

        onAdd() {
          this.add(this.state.add);
        }

        add(value) {
          if (!value.length) return;
          const controller = this.props.controller;

          try {
            if (controller.has(value)) window.alert(tr("Value already in list: {value}", {
              value
            }));else this.setState({
              add: ""
            }, () => controller.add(value));
          } catch (exception) {
            window.alert(exception.toString());
          }
        }

        remove(value) {
          const controller = this.props.controller;

          try {
            if (controller.has(value)) controller.remove(value);
          } catch (e) {
            window.alert(e.toString());
          }
        }

      });

      SetInput.contextType = LangContext;
      SetInput.propTypes = {
        controller: PropTypes.instanceOf(SetController),
        identifier: PropTypes.string,
        values: PropTypes.array,
        className: PropTypes.string
      };
    }
  };
});