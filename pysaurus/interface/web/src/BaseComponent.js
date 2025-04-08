export class BaseComponent extends React.Component {
	constructor(props) {
		super(props);
		this.state = this.getInitialState();
		this.bindMethods();
	}

	getInitialState() {
		return {};
	}

	bindMethods() {
		// Automatically bind all methods of the class
		const methods = Object.getOwnPropertyNames(Object.getPrototypeOf(this)).filter(
			(name) => name !== "constructor" && typeof this[name] === "function"
		);
		methods.forEach((method) => {
			this[method] = this[method].bind(this);
			// console.log(`bound ${method}`);
		});
	}

	setStateAsync(newState) {
		return new Promise((resolve) => this.setState(newState, resolve));
	}
}
