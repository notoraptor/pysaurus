import React from 'react';
import './App.css';
import {Connection} from "./client/connection";
import {Request} from "./client/requests";
import {Helmet} from "react-helmet/es/Helmet";

const HOSTNAME = 'localhost';
const PORT = 8432;

const DATABASE_NOT_LOADED = 0;
const DATABASE_LOADING = 1;
const DATABASE_LOADED = 2;

export class App extends React.Component {
	constructor(props) {
		super(props);
		this.connection = null;
		/** @var Connection this.connection */
		this.state = {
			message_type: null,
			message: null,
			needConnection: true,
			notifications: [],
		};
		this.connect = this.connect.bind(this);
		this.onConnectionClosed = this.onConnectionClosed.bind(this);
		this.loadDatabase = this.loadDatabase.bind(this);
		this.onNotification = this.onNotification.bind(this);
	}

	error(message) {
		this.setState({message_type: 'alert-danger', message: message});
	}

	info(message) {
		this.setState({message_type: 'alert-warning', message: message});
	}

	success(message) {
		this.setState({message_type: 'alert-success', message: message});
	}

	clearMessage() {
		this.setState({message_type: null, message: null});
	}

	connect() {
		let toConnect = false;
		if (this.connection) {
			if (this.connection.isConnecting()) {
				this.info('We are connecting to server.')
			} else if (this.connection.isConnected()) {
				this.info('Already connected!')
			} else {
				toConnect = true;
			}
		} else {
			toConnect = true;
		}
		if (!toConnect)
			return;
		if (this.connection)
			this.connection.reset();
		else {
			this.connection = new Connection(HOSTNAME, PORT);
			this.connection.onClose = this.onConnectionClosed;
			this.connection.onNotification = this.onNotification;
		}
		this.connection.connect()
			.then(() => {
				this.setState({needConnection: false});
				this.success('Connected!');
			})
			.catch((error) => {
				console.log(error);
				this.error(`Unable to connect to ${this.connection.getUrl()}`);
			});
	}

	onConnectionClosed() {
		this.error('Connection closed!');
		this.setState({needConnection: true});
	}

	notConnected() {
		return !this.connection || this.connection.notConnected();
	}

	isConnecting() {
		return this.connection && this.connection.isConnecting();
	}

	isConnected() {
		return this.connection && this.connection.isConnected();
	}

	loadDatabase() {
		if (!this.isConnected())
			return;
		this.connection.send(Request.load())
			.then(response => {
				console.log(response);
				this.info(response);
			})
			.catch(error => {
				console.log(error);
				this.error(`Error while trying to load database: ${error.type}: ${error.message}`);
			})
	}

	onNotification(notification) {
		let string = notification.name + '\r\n';
		const keys = Object.keys(notification.parameters);
		keys.sort();
		for (let key of keys) {
			string += `\t${key}: ${notification.parameters[key]}\r\n`;
		}
		const notifications = this.state.notifications.slice();
		notifications.push(string);
		this.setState({notifications: notifications});
	}

	render() {
		/*
		return (
			<div className="container-fluid" style={{height: '100%'}}>
				<div className="d-flex  flex-column">
					<div>hello</div>
					<div className="flex-grow-1" style={{backgroundColor: 'red'}}>world</div>
				</div>
			</div>
		);
		*/
		return (
			<div className="container-fluid">
				<Helmet>
					<title>Pysaurus!</title>
				</Helmet>
				<div className="d-flex flex-column page">
					<header className="row align-items-center p-2">
						<div className="col-md"><strong>Pysaurus</strong></div>
						<div className="col-md">
							{this.state.message_type ?
								<div className={`alert ${this.state.message_type}`}>{this.state.message}</div> : ''}
						</div>
						<div className="col-md text-md-right">
							{this.state.needConnection ?
								<button className="btn btn-primary" onClick={this.connect}>connect</button> :
								<button className="btn btn-primary" onClick={this.loadDatabase}>load database</button>
							}
						</div>
					</header>
					<div className="loading row flex-grow-1">
						<div className="messages">
							{
								this.state.notifications.map((value, index) => (
									<pre key={index}>{value}</pre>
								))
							}
						</div>
					</div>
				</div>
			</div>
		);
	}
}