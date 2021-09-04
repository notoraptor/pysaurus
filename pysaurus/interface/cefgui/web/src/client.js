import {connect} from "./client/connect.js";
import {createRequest} from "./client/requests.js";

function onOpenSuccess() {
    console.log("Connection opened.");
    System.import("./build/index.js");
}
function onOpenError(error) {
    console.error("Error when connecting.");
    console.error(error);
}
function onClose() {
    console.log("Connection closed.");
}
function onNotification(notification) {
    console.log("Notification received.");
    window.NOTIFICATION_MANAGER.call(notification.parameters);
}

window.CONNECTION = connect(null, {
    onClose: onClose,
    onOpenError: onOpenError,
    onOpenSuccess: onOpenSuccess,
    onNotification: onNotification,
});

window.backend_call = function(name, args) {
    return window.CONNECTION.send(createRequest(name, args));
};
