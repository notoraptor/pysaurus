new QWebChannel(qt.webChannelTransport, function (channel) {
	console.info("Qt loaded.");
	window.backend = channel.objects.backend;
	window.backend_call = function (name, args) {
		return new Promise((resolve, reject) => {
			backend
				.call([name, args])
				.then((result) => {
					if (result.error) {
						reject(result.data);
					} else {
						resolve(result.data);
					}
				})
				.catch((error) => reject({ name: "javascript error", message: error.message }));
		});
	};
	backend.notified.connect(function (notification) {
		window.NOTIFICATION_MANAGER.call(notification);
	});
	System.import("./build/index.js");
});
window.QT = true;
