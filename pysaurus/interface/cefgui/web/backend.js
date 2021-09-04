/**
 * CEF backend.
 */
window.backend_call = function(name, args) {
    return new Promise((resolve, reject) => {
        python.call(name, args, resolve, reject);
    });
};
