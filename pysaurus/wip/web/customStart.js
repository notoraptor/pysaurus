const open = require('open');

// Opens the image in the default image viewer
(async () => {
	// Specify app arguments
	const url = process.argv[process.argv.length - 1];
	await open(url, {app: [
		'C:\\Users\\notoraptor\\Miniconda3\\python.exe', '-m', 'pysaurus.interface.server_instance.cef_python']});
})();
