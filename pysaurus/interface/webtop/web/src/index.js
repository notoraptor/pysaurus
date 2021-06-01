import {App} from "./App.js";
import {python_call} from "./utils/backend.js";

window.onkeydown = function(event) {
    KEYBOARD_MANAGER.call(event);
};

document.body.onunload = function() {
    console.info('GUI closed!');
    python_call('close_app');
};

ReactDOM.render(<App/>, document.getElementById('root'));
