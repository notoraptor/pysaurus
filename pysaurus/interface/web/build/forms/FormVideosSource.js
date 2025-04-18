System.register(["../BaseComponent.js", "../dialogs/FancyBox.js", "../language.js", "../utils/FancyboxManager.js"], function (_export, _context) {
  "use strict";

  var BaseComponent, FancyBox, tr, Fancybox, FormVideosSource;
  function getSubTree(tree, entryName) {
    const steps = entryName.split("-");
    let subTree = tree;
    for (let step of steps) subTree = subTree[step];
    return subTree;
  }
  function collectPaths(tree, collection, prefix = "") {
    if (tree) {
      if (prefix.length) collection.push(prefix);
      for (let name of Object.keys(tree)) {
        const entryName = prefix.length ? prefix + "-" + name : name;
        collectPaths(tree[name], collection, entryName);
      }
    } else {
      collection.push(prefix);
    }
  }
  function addPaths(oldPaths, paths) {
    const newPaths = oldPaths.slice();
    for (let path of paths) {
      if (newPaths.indexOf(path) < 0) {
        newPaths.push(path);
      }
    }
    newPaths.sort();
    return newPaths;
  }
  function removePaths(oldPaths, paths) {
    let newPaths = oldPaths.slice();
    for (let path of paths) {
      const pos = newPaths.indexOf(path);
      if (pos >= 0) {
        newPaths.splice(pos, 1);
      }
    }
    return newPaths;
  }
  _export("FormVideosSource", void 0);
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
      _export("FormVideosSource", FormVideosSource = class FormVideosSource extends BaseComponent {
        // tree
        // sources
        // onClose(sources)

        getInitialState() {
          return {
            paths: this.props.sources.map(path => path.join("-"))
          };
        }
        render() {
          return /*#__PURE__*/React.createElement(FancyBox, {
            title: "Select Videos"
          }, this.renderTree(this.props.tree), /*#__PURE__*/React.createElement("p", null, this.state.paths.length ? tr("Currently selected:") : tr("Currently selected: none")), this.state.paths.length ? /*#__PURE__*/React.createElement("ul", null, this.state.paths.map((path, index) => /*#__PURE__*/React.createElement("li", {
            key: index
          }, /*#__PURE__*/React.createElement("strong", null, path.replace(/-/g, "."))))) : "", /*#__PURE__*/React.createElement("p", {
            className: "submit mx-1 my-4"
          }, /*#__PURE__*/React.createElement("button", {
            className: "submit block",
            onClick: this.submit
          }, tr("select"))));
        }
        renderTree(tree, prefix = "") {
          return /*#__PURE__*/React.createElement("ul", null, Object.keys(tree).map((name, index) => {
            const subTree = tree[name];
            const entryName = prefix.length ? prefix + "-" + name : name;
            const hasPath = this.hasPath(entryName);
            return /*#__PURE__*/React.createElement("li", {
              key: index
            }, subTree ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("strong", null, name), " ", /*#__PURE__*/React.createElement("input", {
              type: "radio",
              onChange: this.onChangeRadio,
              id: entryName + "0",
              name: entryName,
              value: "select",
              checked: hasPath
            }), " ", /*#__PURE__*/React.createElement("label", {
              htmlFor: entryName + "0"
            }, "select"), " ", /*#__PURE__*/React.createElement("input", {
              type: "radio",
              onChange: this.onChangeRadio,
              id: entryName + "1",
              name: entryName,
              value: "develop",
              checked: !hasPath
            }), " ", /*#__PURE__*/React.createElement("label", {
              htmlFor: entryName + "1"
            }, tr("develop"))), hasPath ? "" : this.renderTree(subTree, entryName)) : /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("label", {
              htmlFor: entryName + "0"
            }, /*#__PURE__*/React.createElement("strong", null, name)), " ", /*#__PURE__*/React.createElement("input", {
              type: "checkbox",
              onChange: this.onChangeCheckBox,
              id: entryName + "0",
              name: entryName,
              checked: hasPath
            })));
          }));
        }
        hasPath(path) {
          return this.state.paths.indexOf(path) >= 0;
        }
        onChangeRadio(event) {
          const element = event.target;
          const name = element.name;
          const value = element.value;
          if (value === "select") {
            const pathsToRemove = [];
            collectPaths(getSubTree(this.props.tree, name), pathsToRemove, name);
            let paths = removePaths(this.state.paths, pathsToRemove);
            paths = addPaths(paths, [name]);
            this.setState({
              paths
            });
          } else if (value === "develop") {
            const paths = removePaths(this.state.paths, [name]);
            this.setState({
              paths
            });
          }
        }
        onChangeCheckBox(event) {
          const element = event.target;
          const name = element.name;
          let paths;
          if (element.checked) {
            paths = addPaths(this.state.paths, [name]);
          } else {
            paths = removePaths(this.state.paths, [name]);
          }
          this.setState({
            paths
          });
        }
        submit() {
          Fancybox.close();
          if (this.state.paths.length) this.props.onClose(this.state.paths.map(path => path.split("-")));
        }
      });
    }
  };
});