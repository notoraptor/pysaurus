import { App } from "./App.js";
import { Callbacks } from "./utils/Callbacks.js";
import { python_call } from "./utils/backend.js";

/** NOTIFICATION_MANAGER.call is called from Python to send notifications to interface. */
window.NOTIFICATION_MANAGER = new Callbacks();

/** Global keyboard manager. Used to react on shortcuts. */
window.KEYBOARD_MANAGER = new Callbacks();

window.onkeydown = function (event) {
	KEYBOARD_MANAGER.call(event);
};

document.body.onunload = function () {
	console.info("GUI closed!");
	python_call("close_app");
};

ReactDOM.render(<App />, document.getElementById("root"));
