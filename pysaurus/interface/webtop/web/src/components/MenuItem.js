export class MenuItem extends React.Component {
    constructor(props) {
        // className? str
        // shortcut? str
        // action? function()
        super(props);
        this.onClick = this.onClick.bind(this);
    }

    render() {
        const classNames = ["menu-item horizontal"];
        if (this.props.className)
            classNames.push(this.props.className);
        return (
            <div className={classNames.join(' ')} onClick={this.onClick}>
                <div className="icon"/>
                <div className="text horizontal">
                    <div className="title">{this.props.children}</div>
                    <div className="shortcut">{this.props.shortcut || ''}</div>
                </div>
            </div>
        );
    }

    onClick() {
        if (this.props.action)
            this.props.action();
    }
}
MenuItem.propTypes = {
    className: PropTypes.string,
    shortcut: PropTypes.string,
    action: PropTypes.func.isRequired, // action()
};
