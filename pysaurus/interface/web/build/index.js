System.register(["./App.js", "./utils/FancyboxManager.js", "./utils/Callbacks.js", "./utils/backend.js", "./utils/functions.js"], function (_export, _context) {
  "use strict";

  var App, FancyboxManager, Callbacks, python_call, IdGenerator, underlineRule, rules, rawBuiltParser, parse, reactOutput;
  return {
    setters: [function (_AppJs) {
      App = _AppJs.App;
    }, function (_utilsFancyboxManagerJs) {
      FancyboxManager = _utilsFancyboxManagerJs.FancyboxManager;
    }, function (_utilsCallbacksJs) {
      Callbacks = _utilsCallbacksJs.Callbacks;
    }, function (_utilsBackendJs) {
      python_call = _utilsBackendJs.python_call;
    }, function (_utilsFunctionsJs) {
      IdGenerator = _utilsFunctionsJs.IdGenerator;
    }],
    execute: function () {
      /** Global fancybox manager. Used to open/close a fancybox.s */
      window.Fancybox = new FancyboxManager("fancybox");
      /** NOTIFICATION_MANAGER.call is called from Python to send notifications to interface. */

      window.NOTIFICATION_MANAGER = new Callbacks();
      /** Global keyboard manager. Used to react on shortcuts. */

      window.KEYBOARD_MANAGER = new Callbacks();
      /** Global state. **/

      window.APP_STATE = {
        videoHistory: new Set(),
        idGenerator: new IdGenerator(),
        latestMoveFolder: null
      }; //

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
          }, output(node.content)); // return React.DOM.u(null, output(node.content));
        }
      };
      rules = Object.assign({}, SimpleMarkdown.defaultRules, {
        underline: underlineRule
      });
      rawBuiltParser = SimpleMarkdown.parserFor(rules);

      parse = function (source, inline = false) {
        var blockSource = source + "\n\n";
        return rawBuiltParser(blockSource, {
          inline
        });
      }; // You probably only need one of these: choose depending on
      // whether you want react nodes or an html string:


      reactOutput = SimpleMarkdown.outputFor(rules, 'react'); // console.log(JSON.stringify(reactOutput(parse("Hello !!world!! !"))));
      //

      window.markdownToReact = function (text, inline = false) {
        // return SimpleMarkdown.defaultReactOutput(SimpleMarkdown.defaultBlockParse(text));
        return reactOutput(parse(text, inline));
      };

      window.onkeydown = function (event) {
        KEYBOARD_MANAGER.call(event);
      };

      document.body.onunload = function () {
        console.info('GUI closed!');
        python_call('close_app');
      };

      ReactDOM.render( /*#__PURE__*/React.createElement(App, null), document.getElementById('root'));
    }
  };
});