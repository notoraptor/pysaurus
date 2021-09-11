import {Connection} from "./connection.js";

const CONFIG = {
    HOSTNAME: 'localhost',
    PORT: 8432,
};

/**
 *
 * @param connection {Connection}
 * @param callbacks {{onClose, onNotification, onOpenSuccess, onOpenError}}
 * @returns {Connection}
 */
export function connect(connection, callbacks) {
    let toConnect = true;
    if (connection) {
        if (connection.status === ConnectionStatus.CONNECTING) {
            toConnect = false;
            console.log('We are connecting to server.');
        } else if (connection.status === ConnectionStatus.CONNECTED) {
            toConnect = false;
            console.log('Already connected!');
        }
    }
    if (!toConnect)
        return connection;
    // Connecting.
    if (connection)
        connection.reset();
    else {
        connection = new Connection(CONFIG.HOSTNAME, CONFIG.PORT);
        if (callbacks.onClose)
            connection.onClose = callbacks.onClose;
        if (callbacks.onNotification)
            connection.onNotification = callbacks.onNotification;
    }
    connection.connect()
        .then(() => {
            if (callbacks.onOpenSuccess)
                callbacks.onOpenSuccess();
        })
        .catch((error) => {
            console.error(`Unable to connect to ${connection.getUrl()}`);
            if (callbacks.onOpenError)
                callbacks.onOpenError(error);
        });
    return connection;
}
