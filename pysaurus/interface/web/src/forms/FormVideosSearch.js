import { BaseComponent } from "../BaseComponent.js";
import { FancyBox } from "../dialogs/FancyBox.js";
import { tr } from "../language.js";
import { Fancybox } from "../utils/FancyboxManager.js";

export class FormVideosSearch extends BaseComponent {
	// text
	// cond
	// onClose(criterion)

	getInitialState() {
		return {
			text: this.props.text || "",
			cond: this.props.cond || "",
		};
	}

	render() {
		return (
			<FancyBox title={tr("Search videos")}>
				<div className="form-videos-search text-center">
					{tr(
						`
Type text to search and choose how to search.

You can also type text and then press enter
to automatically select "AND" as search method.
`,
						null,
						"markdown",
					)}
					<p>
						<input
							type="text"
							id="input-search"
							className="block mb-2"
							name="searchText"
							placeholder="Search ..."
							onFocus={this.onFocusInput}
							onChange={this.onChangeInput}
							onKeyDown={this.onInput}
							value={this.state.text}
						/>
					</p>
					<p>
						<input
							type="radio"
							id="input-search-and"
							name="searchType"
							value="and"
							onChange={this.onChangeCond}
							checked={this.state.cond === "and"}
						/>
						<label htmlFor="input-search-and">{tr("all terms")}</label>
					</p>
					<p>
						<input
							type="radio"
							id="input-search-or"
							name="searchType"
							value="or"
							onChange={this.onChangeCond}
							checked={this.state.cond === "or"}
						/>
						<label htmlFor="input-search-or">{tr("any term")}</label>
					</p>
					<p>
						<input
							type="radio"
							id="input-search-exact"
							name="searchType"
							value="exact"
							onChange={this.onChangeCond}
							checked={this.state.cond === "exact"}
						/>
						<label htmlFor="input-search-exact">{tr("exact sentence")}</label>
					</p>
					<p>
						<input
							type="radio"
							id="input-search-id"
							name="searchType"
							value="id"
							onChange={this.onChangeCond}
							checked={this.state.cond === "id"}
						/>
						<label htmlFor="input-search-id">{tr("video ID")}</label>
					</p>
				</div>
			</FancyBox>
		);
	}

	componentDidMount() {
		document.querySelector("#input-search").focus();
	}

	onFocusInput(event) {
		event.target.select();
	}

	onChangeInput(event) {
		this.setState({ text: event.target.value, cond: "" });
	}

	onChangeCond(event) {
		const text = this.state.text;
		const cond = event.target.value;
		this.setState({ text, cond }, () => {
			if (text.length && cond.length) this.onClose({ text, cond });
		});
	}

	onInput(event) {
		if (event.key === "Enter") {
			if (this.state.text.length) {
				const text = this.state.text;
				const cond = "and";
				this.onClose({ text, cond });
				return true;
			}
		}
	}

	onClose(criterion) {
		Fancybox.close();
		this.props.onClose(criterion);
	}
}
