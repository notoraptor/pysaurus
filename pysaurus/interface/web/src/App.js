import React from 'react';
import './App.css';
import {Connection} from "./core/connection";


export class App extends React.Component {
	constructor(props) {
		super(props);
		this.connection = null;
		this.state = {
			error: null,
			message: null
		};
		this.onConnectionClosed = this.onConnectionClosed.bind(this);
	}

	render() {
		return (
			<div className="container">
				<p>Hello World!</p>
				{this.state.error ? <p className="alert alert-danger">{this.state.error}</p> : ''}
				{this.state.message ? <p className="alert alert-success">{this.state.message}</p> : ''}
			</div>
		);
	}

	onConnectionClosed() {
		this.setState({error: 'Connection closed!', message: null});
	}

	componentDidMount() {
		if (this.connection)
			return;
		this.connection = new Connection('localhost', 8432);
		this.connection.onClose = this.onConnectionClosed;
		this.connection.connect()
			.then(() => this.setState({message: 'Connected!', error: null}))
			.catch((error) => {
				console.log(error);
				this.setState({error: `Unable to connect to ${this.connection.getUrl()}`, message: null})
			})
	}
}