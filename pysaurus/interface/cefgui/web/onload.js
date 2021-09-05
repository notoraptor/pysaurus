window.onload = function() {
    console.log("Frontent on load.");
    if (!window.backend_call) {
        /* CEF backend. */
        window.backend_call = function(name, args) {
            return new Promise((resolve, reject) => {
                python.call(name, args, resolve, reject);
            });
        };
        System.import('./build/index.js');
    }
};
