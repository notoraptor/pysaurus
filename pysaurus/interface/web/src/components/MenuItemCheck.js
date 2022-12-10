export class MenuItemCheck extends React.Component {
	constructor(props) {
		// action? function(checked)
		// checked? bool
		super(props);
		this.onClick = this.onClick.bind(this);
	}

	render() {
		const checked = !!this.props.checked;
		return (
			<div className="menu-item horizontal" onClick={this.onClick}>
				<div className="icon">
					<div className="border">
						<div className={"check " + (checked ? "checked" : "not-checked")} />
					</div>
				</div>
				<div className="text">{this.props.children}</div>
			</div>
		);
	}

	onClick() {
		const checked = !this.props.checked;
		if (this.props.action) this.props.action(checked);
	}
}
