System.register([], function (_export, _context) {
  "use strict";

  var underlineRule, rules, rawBuiltParser, parse, reactOutput;
  function markdownToReact(text, inline = false) {
    // return SimpleMarkdown.defaultReactOutput(SimpleMarkdown.defaultBlockParse(text));
    return reactOutput(parse(text, inline));
  }
  _export("markdownToReact", markdownToReact);
  return {
    setters: [],
    execute: function () {
      underlineRule = {
        // Specify the order in which this rule is to be run
        order: SimpleMarkdown.defaultRules.em.order - 0.5,
        // First we check whether a string matches
        match: function (source) {
          return /^!!([\s\S]+?)!!/.exec(source);
        },
        // Then parse this string into a syntax node
        parse: function (capture, parse, state) {
          return {
            content: parse(capture[1], state)
          };
        },
        // Finally transform this syntax node into a
        // React element
        react: function (node, output) {
          return React.createElement("strong", {
            className: "red-flag"
          }, output(node.content));
          // return React.DOM.u(null, output(node.content));
        }
      };
      rules = Object.assign({}, SimpleMarkdown.defaultRules, {
        underline: underlineRule
      });
      rawBuiltParser = SimpleMarkdown.parserFor(rules);
      parse = function (source, inline = false) {
        const blockSource = source + "\n\n";
        return rawBuiltParser(blockSource, {
          inline
        });
      }; // You probably only need one of these: choose depending on
      // whether you want react nodes or an html string:
      reactOutput = SimpleMarkdown.outputFor(rules, "react");
    }
  };
});