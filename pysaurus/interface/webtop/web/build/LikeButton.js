System.register([], function (_export, _context) {
  "use strict";

  var LikeButton;

  _export("LikeButton", void 0);

  return {
    setters: [],
    execute: function () {
      _export("LikeButton", LikeButton = class LikeButton extends React.Component {
        constructor(props) {
          super(props);
          this.state = {
            liked: false
          };
        }

        render() {
          python.get_name(name => python.print('Called from javascript:', name));

          if (this.state.liked) {
            return 'You liked this.';
          }

          return /*#__PURE__*/React.createElement("button", {
            onClick: () => this.setState({
              liked: true
            })
          }, "Like");
        }

      });
    }
  };
});