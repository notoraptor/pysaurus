import { BaseComponent } from "../BaseComponent.js";
import { Cell } from "../components/Cell.js";
import { Fancybox } from "../utils/FancyboxManager.js";
import { Dialog } from "./Dialog.js";

export class DialogSearch extends BaseComponent {
	getInitialState() {
		return {
			text: "",
		};
	}

	render() {
		return (
			<Dialog title={this.props.title} yes={"go"} action={this.onClose}>
				<Cell center={true} full={true} className="text-center">
					<input
						type="text"
						id="input-search"
						placeholder="Search ..."
						onFocus={this.onFocusInput}
						onChange={this.onChangeInput}
						onKeyDown={this.onInput}
						value={this.state.text}
					/>
				</Cell>
			</Dialog>
		);
	}

	componentDidMount() {
		document.querySelector("#input-search").focus();
	}

	onFocusInput(event) {
		event.target.select();
	}

	onChangeInput(event) {
		this.setState({ text: event.target.value });
	}

	onInput(event) {
		if (event.key === "Enter" && this.state.text) {
			Fancybox.close();
			this.props.onSearch(this.state.text);
			return true;
		}
	}

	onClose() {
		if (this.state.text) this.props.onSearch(this.state.text);
	}
}

DialogSearch.propTypes = {
	title: PropTypes.string.isRequired,
	// onSearch(str)
	onSearch: PropTypes.func.isRequired,
};
