import { Dialog } from "../dialogs/Dialog.js";
import { LangContext, tr } from "../language.js";
import { Fancybox } from "../utils/FancyboxManager.js";

export class GenericFormRename extends React.Component {
	constructor(props) {
		super(props);
		this.state = { data: this.props.data };
		this.onChange = this.onChange.bind(this);
		this.onKeyDown = this.onKeyDown.bind(this);
		this.submit = this.submit.bind(this);
		this.onFocusInput = this.onFocusInput.bind(this);
	}

	render() {
		return (
			<Dialog title={this.props.title} yes={tr("rename")} action={this.submit}>
				<div className="form-rename text-center">
					<h1>{this.props.header}</h1>
					<h2>
						<code id="filename">{this.props.description}</code>
					</h2>
					<p className="form">
						<input
							type="text"
							id="name"
							className="block"
							value={this.state.data}
							onChange={this.onChange}
							onKeyDown={this.onKeyDown}
							onFocus={this.onFocusInput}
						/>
					</p>
				</div>
			</Dialog>
		);
	}

	componentDidMount() {
		document.querySelector("input#name").focus();
	}

	onFocusInput(event) {
		event.target.select();
	}

	onChange(event) {
		this.setState({ data: event.target.value });
	}

	onKeyDown(event) {
		if (event.key === "Enter") {
			Fancybox.close();
			this.submit();
		}
	}

	submit() {
		if (this.state.data && this.state.data !== this.props.data) this.props.onClose(this.state.data);
	}
}

GenericFormRename.propTypes = {
	title: PropTypes.string.isRequired,
	header: PropTypes.string.isRequired,
	description: PropTypes.string.isRequired,
	data: PropTypes.string.isRequired,
	onClose: PropTypes.func.isRequired,
};
GenericFormRename.contextType = LangContext;
