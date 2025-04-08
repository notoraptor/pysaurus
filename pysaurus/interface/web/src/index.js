import { App } from "./App.js";
import { Callbacks } from "./utils/Callbacks.js";
import { NotificationManager } from "./utils/NotificationManager.js";
import { Backend } from "./utils/backend.js";

/** NOTIFICATION_MANAGER.call is called from Python to send notifications to interface. */
window.NOTIFICATION_MANAGER = new NotificationManager();

/** Global keyboard manager. Used to react on shortcuts. */
window.KEYBOARD_MANAGER = new Callbacks();

window.onkeydown = function (event) {
	KEYBOARD_MANAGER.call(event);
};

if (!window.QT) {
	document.body.onunload = function () {
		console.info("GUI closed!");
		Backend.close_app();
	};
}

backend_call("get_constants", []).then((constants) => {
	for (let entry of Object.entries(constants)) {
		const [name, value] = entry;
		window[name] = value;
		// console.log(["CONSTANT", name, value]);
	}
	const root = ReactDOM.createRoot(document.getElementById("root"));
	root.render(<App />);
});
