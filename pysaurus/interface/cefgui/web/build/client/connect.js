System.register(["./connection.js"], function (_export, _context) {
  "use strict";

  var Connection, CONFIG;

  /**
   *
   * @param connection {Connection}
   * @param callbacks {{onClose, onNotification, onOpenSuccess, onOpenError}}
   * @returns {Connection}
   */
  function connect(connection, callbacks) {
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

    if (!toConnect) return connection; // Connecting.

    if (connection) connection.reset();else {
      connection = new Connection(CONFIG.HOSTNAME, CONFIG.PORT);
      if (callbacks.onClose) connection.onClose = callbacks.onClose;
      if (callbacks.onNotification) connection.onNotification = callbacks.onNotification;
    }
    connection.connect().then(() => {
      if (callbacks.onOpenSuccess) callbacks.onOpenSuccess();
    }).catch(error => {
      console.error(`Unable to connect to ${connection.getUrl()}`);
      if (callbacks.onOpenError) callbacks.onOpenError(error);
    });
    return connection;
  }

  _export("connect", connect);

  return {
    setters: [function (_connectionJs) {
      Connection = _connectionJs.Connection;
    }],
    execute: function () {
      CONFIG = {
        HOSTNAME: 'localhost',
        PORT: 8432
      };
    }
  };
});