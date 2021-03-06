import {App} from "./App.js";
import {FancyboxManager} from "./utils/FancyboxManager.js";
import {Callbacks} from "./utils/Callbacks.js";
import {python_call} from "./utils/backend.js";

/** Global fancybox manager. Used to open/close a fancybox.s */
window.Fancybox = new FancyboxManager("fancybox");

/** NOTIFICATION_MANAGER.call is called from Python to send notifications to interface. */
window.NOTIFICATION_MANAGER = new Callbacks();

/** Global keyboard manager. Used to react on shortcuts. */
window.KEYBOARD_MANAGER = new Callbacks();

/** Global state. **/
window.APP_STATE = {
    videoHistory: new Set()
};

window.onkeydown = function (event) {
    KEYBOARD_MANAGER.call(event);
};

document.body.onunload = function () {
    console.info('GUI closed!');
    python_call('close_app');
};

ReactDOM.render(<App/>, document.getElementById('root'));
