/* pywebview backend. */
window.addEventListener('pywebviewready', function() {
    console.log("Pywebview loaded.");
    window.backend_call = function(name, args) {
        return pywebview.api.call(name, args);
    };
    System.import('./build/index.js');
});
