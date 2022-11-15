import { FormPaginationGoTo } from "../forms/FormPaginationGoTo.js";
import { DialogSearch } from "../dialogs/DialogSearch.js";
import { capitalizeFirstLetter } from "../utils/functions.js";

export class Pagination extends React.Component {
	constructor(props) {
		// singular: str
		// plural: str
		// nbPages: int
		// pageNumber: int
		// onChange: function(int)
		// onSearch? function(str)
		super(props);
		this.onFirst = this.onFirst.bind(this);
		this.onNext = this.onNext.bind(this);
		this.onLast = this.onLast.bind(this);
		this.onPrevious = this.onPrevious.bind(this);
		this.go = this.go.bind(this);
		this.look = this.look.bind(this);
	}

	render() {
		const singular = this.props.singular;
		const plural = this.props.plural;
		const nbPages = this.props.nbPages;
		const pageNumber = this.props.pageNumber;
		return nbPages ? (
			<span className="navigation py-1 text-center">
				<button
					className="first"
					disabled={pageNumber === 0}
					onClick={this.onFirst}>
					&lt;&lt;
				</button>
				<button
					className="previous"
					disabled={pageNumber === 0}
					onClick={this.onPrevious}>
					&lt;
				</button>
				<span
					{...(this.props.onSearch
						? { className: "go", onClick: this.look }
						: {})}>
					{capitalizeFirstLetter(singular)}
				</span>
				<span className="go clickable" onClick={this.go}>
					{pageNumber + 1}/{nbPages}
				</span>
				<button
					className="next"
					disabled={pageNumber === nbPages - 1}
					onClick={this.onNext}>
					&gt;
				</button>
				<button
					className="last"
					disabled={pageNumber === nbPages - 1}
					onClick={this.onLast}>
					&gt;&gt;
				</button>
			</span>
		) : (
			<span className="navigation py-1 text-center">
				<em>0 {plural}</em>
			</span>
		);
	}

	onFirst() {
		if (this.props.pageNumber !== 0) {
			this.props.onChange(0);
		}
	}

	onPrevious() {
		if (this.props.pageNumber > 0) {
			this.props.onChange(this.props.pageNumber - 1);
		}
	}

	onNext() {
		if (this.props.pageNumber < this.props.nbPages - 1) {
			this.props.onChange(this.props.pageNumber + 1);
		}
	}

	onLast() {
		if (this.props.pageNumber !== this.props.nbPages - 1) {
			this.props.onChange(this.props.nbPages - 1);
		}
	}

	go() {
		Fancybox.load(
			<FormPaginationGoTo
				nbPages={this.props.nbPages}
				pageNumber={this.props.pageNumber}
				onClose={(pageNumber) => {
					if (pageNumber !== this.props.pageNumber)
						this.props.onChange(pageNumber);
				}}
			/>
		);
	}

	look() {
		Fancybox.load(
			<DialogSearch title={"Search first:"} onSearch={this.props.onSearch} />
		);
	}
}
