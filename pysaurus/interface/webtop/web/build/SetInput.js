System.register([], function (_export, _context) {
  "use strict";

  var SetController, ComponentController, SetInput;

  function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

  _export({
    ComponentController: void 0,
    SetInput: void 0
  });

  return {
    setters: [],
    execute: function () {
      SetController = class SetController {
        constructor() {}

        size() {}

        get(index) {}

        has(value) {}

        add(value) {}

        remove(value) {}

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
          return this.app.state[this.field].indexOf(value) >= 0;
        }

        add(value) {
          const arr = this.app.state[this.field].slice();

          if (this.parser) {
            const parsedValue = this.parser(value);
            if (parsedValue !== undefined) arr.push(parsedValue);
          } else {
            arr.push(value);
          }

          this.app.setState({
            [this.field]: arr
          });
        }

        remove(toRemove) {
          const arr = [];

          for (let value of this.app.state[this.field]) {
            if (value !== toRemove) arr.push(value);
          }

          this.app.setState({
            [this.field]: arr
          });
        }

      });

      _export("SetInput", SetInput = class SetInput extends React.Component {
        constructor(props) {
          // controller: SetController
          // identifier? str
          // values
          // onCheck? function(value)
          super(props);
          this.state = {
            add: this.props.values ? this.props.values[0] : ''
          };
          this.onChangeAdd = this.onChangeAdd.bind(this);
          this.onInputAdd = this.onInputAdd.bind(this);
          this.onAdd = this.onAdd.bind(this);
          this.add = this.add.bind(this);
          this.remove = this.remove.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement("div", {
            className: "set-input"
          }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("tbody", null, this.renderList(), /*#__PURE__*/React.createElement("tr", {
            className: "form"
          }, /*#__PURE__*/React.createElement("td", {
            className: "input"
          }, this.props.values ? /*#__PURE__*/React.createElement("select", {
            name: "add",
            value: this.state.add,
            onChange: this.onChangeAdd
          }, this.props.values.map((value, index) => /*#__PURE__*/React.createElement("option", {
            key: index,
            value: value
          }, value))) : /*#__PURE__*/React.createElement("input", _extends({
            type: "text",
            name: "add",
            value: this.state.add,
            onChange: this.onChangeAdd,
            onKeyDown: this.onInputAdd,
            size: "10"
          }, this.props.identifier ? {
            id: this.props.identifier
          } : {}))), /*#__PURE__*/React.createElement("td", {
            className: "action"
          }, /*#__PURE__*/React.createElement("button", {
            className: "add",
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
            }, /*#__PURE__*/React.createElement("td", {
              className: "label"
            }, value), /*#__PURE__*/React.createElement("td", {
              className: "action"
            }, /*#__PURE__*/React.createElement("button", {
              className: "remove",
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
          if (value.length && (!this.props.onCheck || this.props.onCheck(value))) {
            const controller = this.props.controller;
            if (controller.has(value)) return window.alert(`Value already in list: ${value}`);
            this.setState({
              add: ''
            }, () => controller.add(value));
          }
        }

        remove(value) {
          const controller = this.props.controller;

          if (controller.has(value)) {
            controller.remove(value);
          }
        }

      });
    }
  };
});