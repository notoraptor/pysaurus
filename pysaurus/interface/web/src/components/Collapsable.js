import { Characters } from "../utils/constants.js";

export class Collapsable extends React.Component {
	constructor(props) {
		super(props);
		this.state = { stack: false };
		this.stack = this.stack.bind(this);
	}

	render() {
		const lite = this.props.lite !== undefined ? this.props.lite : true;
		return (
			<div
				className={`abstract-collapsable ${lite ? "collapsable" : "stack"} ${
					this.props.className || ""
				}`}>
				<div className="header clickable horizontal" onClick={this.stack}>
					<div className="title">{this.props.title}</div>
					<div className="icon">
						{this.state.stack ? Characters.ARROW_DOWN : Characters.ARROW_UP}
					</div>
				</div>
				{this.state.stack ? (
					""
				) : (
					<div className="content">{this.props.children}</div>
				)}
			</div>
		);
	}

	stack() {
		this.setState({ stack: !this.state.stack });
	}
}

Collapsable.propTypes = {
	title: PropTypes.string,
	className: PropTypes.string,
	lite: PropTypes.bool,
};
