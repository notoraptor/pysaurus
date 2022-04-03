new QWebChannel(qt.webChannelTransport, function (channel) {
    window.backend = channel.objects.backend;
    window.backend_call = function (name, ...args) {
        return new Promise((resolve, reject) => {
            backend.call(JSON.stringify([name, args]))
                .then(raw => {
                    const result = JSON.parse(raw);
                    if (result.error) {
                        reject(result.data);
                    } else {
                        resolve(result.data);
                    }
                })
                .catch(error => reject({name: "javascript error", message: error.message}));
        });
    }
});
