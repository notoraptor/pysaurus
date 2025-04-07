window.onload = function () {
	if (window.python && !window.backend_call) {
		/* CEF backend. */
		console.log("CEF loaded.");
		window.backend_call = function (name, args) {
			return new Promise((resolve, reject) => {
				python.call(name, args, resolve, reject);
			});
		};
		System.import("./build/index.js");
	}
};
