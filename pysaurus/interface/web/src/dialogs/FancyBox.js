import { Fancybox } from "../utils/FancyboxManager.js";

export class FancyBox extends React.Component {
	/**
	 * @param props {{title: str}}
	 */
	constructor(props) {
		// title, onClose() ?, children
		super(props);
		this.callbackIndex = -1;
		this.checkShortcut = this.checkShortcut.bind(this);
		this.onClose = this.onClose.bind(this);
	}

	render() {
		return (
			<div className="fancybox-wrapper absolute-plain">
				<div className="fancybox vertical">
					<div className="fancybox-header flex-shrink-0 horizontal p-2">
						<div
							className="fancybox-title flex-grow-1 text-center"
							title={this.props.title}>
							<strong>{this.props.title}</strong>
						</div>
						<div className="pl-2">
							<button onClick={this.onClose}>&times;</button>
						</div>
					</div>
					<div className="fancybox-content position-relative overflow-auto flex-grow-1 p-2">
						{this.props.children}
					</div>
				</div>
			</div>
		);
	}

	componentDidMount() {
		this.callbackIndex = KEYBOARD_MANAGER.register(this.checkShortcut);
	}

	componentWillUnmount() {
		KEYBOARD_MANAGER.unregister(this.callbackIndex);
	}

	/**
	 * @param event {KeyboardEvent}
	 */
	checkShortcut(event) {
		if (event.key === "Escape") {
			this.onClose();
			return true;
		}
	}

	onClose() {
		if (!this.props.onClose || this.props.onClose()) Fancybox.close();
	}
}

FancyBox.propTypes = {
	title: PropTypes.string.isRequired,
	// onClose()
	onClose: PropTypes.func,
};
