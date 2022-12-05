import { FancyBox } from "./FancyBox.js";
import { LangContext, tr } from "../language.js";
import { Fancybox } from "../utils/FancyboxManager.js";

export class Dialog extends React.Component {
	constructor(props) {
		super(props);
		this.yes = this.yes.bind(this);
	}

	render() {
		return (
			<FancyBox title={this.props.title}>
				<div className="dialog absolute-plain vertical">
					<div className="position-relative flex-grow-1 overflow-auto p-2 vertical">
						{this.props.children}
					</div>
					<div className="buttons flex-shrink-0 horizontal">
						<div className="button flex-grow-1 p-2 yes">
							<button className="block bold" onClick={this.yes}>
								{this.props.yes || tr("yes")}
							</button>
						</div>
						<div className="button flex-grow-1 p-2 no">
							<button className="block bold" onClick={Fancybox.close}>
								{this.props.no || tr("cancel")}
							</button>
						</div>
					</div>
				</div>
			</FancyBox>
		);
	}

	yes() {
		Fancybox.close();
		if (this.props.action) this.props.action();
	}
}

Dialog.contextType = LangContext;
Dialog.propTypes = {
	title: PropTypes.string.isRequired,
	// action()
	action: PropTypes.func,
	yes: PropTypes.string,
	no: PropTypes.string,
};
