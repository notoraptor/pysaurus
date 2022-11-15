new QWebChannel(qt.webChannelTransport, function (channel) {
	console.info("Qt loaded.");
	window.backend = channel.objects.backend;
	window.backend_call = function (name, args) {
		return new Promise((resolve, reject) => {
			backend
				.call(JSON.stringify([name, args]))
				.then((raw) => {
					const result = JSON.parse(raw);
					if (result.error) {
						reject(result.data);
					} else {
						resolve(result.data);
					}
				})
				.catch((error) =>
					reject({ name: "javascript error", message: error.message })
				);
		});
	};
	backend.notified.connect(function (raw) {
		const notification = JSON.parse(raw);
		window.NOTIFICATION_MANAGER.call(notification);
	});
	backend_call("get_constants", []).then((constants) => {
		for (let entry of Object.entries(constants)) {
			const [name, value] = entry;
			window[name] = value;
		}
		System.import("./build/index.js");
	});
});
