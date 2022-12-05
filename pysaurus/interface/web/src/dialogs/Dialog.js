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
							<button className="block" onClick={this.yes}>
								<strong>{this.props.yes || tr("yes")}</strong>
							</button>
						</div>
						<div className="button flex-grow-1 p-2 no">
							<button className="block" onClick={Fancybox.close}>
								<strong>{this.props.no || tr("cancel")}</strong>
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
