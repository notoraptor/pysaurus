System.register(["./Dialog.js"], function (_export, _context) {
  "use strict";

  var Dialog, FormPropertyMultiVideo;

  _export("FormPropertyMultiVideo", void 0);

  return {
    setters: [function (_DialogJs) {
      Dialog = _DialogJs.Dialog;
    }],
    execute: function () {
      _export("FormPropertyMultiVideo", FormPropertyMultiVideo = class FormPropertyMultiVideo extends React.Component {
        constructor(props) {
          // nbVideos
          // definition: property definition
          // values: [(value, count)]
          // onClose
          super(props);
          const mapping = new Map();
          const current = [];

          for (let valueAndCount of this.props.values) {
            mapping.set(valueAndCount[0], valueAndCount[1]);
            current.push(valueAndCount[0]);
          }

          this.state = {
            mapping: mapping,
            current: current,
            add: [],
            remove: [],
            value: null
          };
          this.onEdit = this.onEdit.bind(this);
          this.onEditKeyDown = this.onEditKeyDown.bind(this);
          this.onAddNewValue = this.onAddNewValue.bind(this);
          this.remove = this.remove.bind(this);
          this.add = this.add.bind(this);
          this.unRemove = this.unRemove.bind(this);
          this.unAdd = this.unAdd.bind(this);
          this.onClose = this.onClose.bind(this);
        }

        render() {
          return /*#__PURE__*/React.createElement(Dialog, {
            yes: "edit",
            no: "cancel",
            onClose: this.onClose
          }, /*#__PURE__*/React.createElement("div", {
            className: "form-property-multi-video"
          }, /*#__PURE__*/React.createElement("div", {
            className: "bar titles horizontal"
          }, /*#__PURE__*/React.createElement("div", null, "To remove"), /*#__PURE__*/React.createElement("div", null, "Current"), /*#__PURE__*/React.createElement("div", null, "To add")), /*#__PURE__*/React.createElement("div", {
            className: "bar panels horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "remove"
          }, this.renderRemove()), /*#__PURE__*/React.createElement("div", {
            className: "current"
          }, this.renderCurrent()), /*#__PURE__*/React.createElement("div", {
            className: "add"
          }, this.renderAdd())), this.renderFormAdd()));
        }

        renderRemove() {
          return this.state.remove.map((value, index) => /*#__PURE__*/React.createElement("div", {
            key: index,
            className: "entry horizontal"
          }, /*#__PURE__*/React.createElement("div", {
            className: "value"
          }, value), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("button", {
            onClick: () => this.unRemove(value)
          }, Utils.CHARACTER_SMART_ARROW_RIGHT))));
        }

        renderCurrent() {
          return this.state.current.map((value, index) => /*#__PURE__*/React.createElement("div", {
            key: index,
            className: "entry horizontal"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: () => this.remove(value)
          }, Utils.CHARACTER_SMART_ARROW_LEFT), /*#__PURE__*/React.createElement("div", {
            className: "value"
          }, value, " ", /*#__PURE__*/React.createElement("em", null, /*#__PURE__*/React.createElement("strong", null, "(", this.state.mapping.get(value), ")"))), /*#__PURE__*/React.createElement("button", {
            onClick: () => this.add(value)
          }, Utils.CHARACTER_SMART_ARROW_RIGHT)));
        }

        renderAdd() {
          return this.state.add.map((value, index) => /*#__PURE__*/React.createElement("div", {
            key: index,
            className: "entry horizontal"
          }, /*#__PURE__*/React.createElement("button", {
            onClick: () => this.unAdd(value)
          }, this.state.mapping.has(value) ? Utils.CHARACTER_SMART_ARROW_LEFT : '-'), /*#__PURE__*/React.createElement("div", {
            className: "value"
          }, value)));
        }

        renderFormAdd() {
          const def = this.props.definition;
          let input;

          if (def.enumeration) {
            input = /*#__PURE__*/React.createElement("select", {
              onChange: this.onEdit
            }, def.enumeration.map((value, valueIndex) => /*#__PURE__*/React.createElement("option", {
              key: valueIndex,
              value: value
            }, value)));
          } else if (def.type === "bool") {
            input = /*#__PURE__*/React.createElement("select", {
              onChange: this.onEdit
            }, /*#__PURE__*/React.createElement("option", {
              value: "false"
            }, "false"), /*#__PURE__*/React.createElement("option", {
              value: "true"
            }, "true"));
          } else {
            input = /*#__PURE__*/React.createElement("input", {
              type: def.type === "int" ? "number" : "text",
              onChange: this.onEdit,
              onKeyDown: this.onEditKeyDown
            });
          }

          return /*#__PURE__*/React.createElement("div", {
            className: "bar new horizontal"
          }, /*#__PURE__*/React.createElement("div", null), /*#__PURE__*/React.createElement("div", null), /*#__PURE__*/React.createElement("div", {
            className: "horizontal"
          }, /*#__PURE__*/React.createElement("div", null, input), /*#__PURE__*/React.createElement("button", {
            className: "add-new-value",
            onClick: this.onAddNewValue
          }, "add")));
        }

        onEdit(event) {
          const def = this.props.definition;

          try {
            this.setState({
              value: parsePropValString(def.type, def.enumeration, event.target.value)
            });
          } catch (exception) {
            window.alert(exception.toString());
          }
        }

        onEditKeyDown(event) {
          if (event.key === "Enter") {
            this.onAddNewValue();
          }
        }

        onAddNewValue() {
          if (this.state.value !== null) {
            if (this.props.definition.multiple) {
              const add = new Set(this.state.add);
              add.add(this.state.value);
              const output = Array.from(add);
              output.sort();
              this.setState({
                add: output
              });
            } else {
              const add = [this.state.value];
              const current = [];
              const remove = Array.from(this.state.mapping);
              remove.sort();
              this.setState({
                remove,
                current,
                add
              });
            }
          }
        }

        remove(value) {
          const current = new Set(this.state.current);
          const remove = new Set(this.state.remove);
          current.delete(value);
          remove.add(value);
          const newCurrent = Array.from(current);
          const newRemove = Array.from(remove);
          newCurrent.sort();
          newRemove.sort();
          this.setState({
            current: newCurrent,
            remove: newRemove
          });
        }

        add(value) {
          if (this.props.definition.multiple) {
            const current = new Set(this.state.current);
            const add = new Set(this.state.add);
            current.delete(value);
            add.add(value);
            const newCurrent = Array.from(current);
            const newAdd = Array.from(add);
            newCurrent.sort();
            newAdd.sort();
            this.setState({
              current: newCurrent,
              add: newAdd
            });
          } else {
            const add = [value];
            const current = [];
            const remove = new Set(this.state.mapping);
            remove.delete(value);
            remove.sort();
            this.setState({
              remove,
              current,
              add
            });
          }
        }

        unRemove(value) {
          const current = new Set(this.state.current);
          const remove = new Set(this.state.remove);
          remove.delete(value);
          current.add(value);
          const newCurrent = Array.from(current);
          const newRemove = Array.from(remove);
          newCurrent.sort();
          newRemove.sort();
          this.setState({
            current: newCurrent,
            remove: newRemove
          });
        }

        unAdd(value) {
          const add = new Set(this.state.add);
          add.delete(value);
          const newAdd = Array.from(add);
          newAdd.sort();

          if (this.state.mapping.has(value)) {
            const current = new Set(this.state.current);
            current.add(value);
            const newCurrent = Array.from(current);
            newCurrent.sort();
            this.setState({
              current: newCurrent,
              add: newAdd
            });
          } else {
            this.setState({
              add: newAdd
            });
          }
        }

        onClose(yes) {
          this.props.onClose(yes ? {
            add: this.state.add,
            remove: this.state.remove
          } : null);
        }

      });
    }
  };
});