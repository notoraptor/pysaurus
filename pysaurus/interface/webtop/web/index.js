System.register(["./LikeButton.js"], function (_export, _context) {
  "use strict";

  var LikeButton;
  return {
    setters: [function (_LikeButtonJs) {
      LikeButton = _LikeButtonJs.LikeButton;
    }],
    execute: function () {
      ReactDOM.render( /*#__PURE__*/React.createElement(LikeButton, null), document.getElementById('root'));
    }
  };
});