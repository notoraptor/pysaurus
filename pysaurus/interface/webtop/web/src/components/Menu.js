export class Menu extends React.Component {
    constructor(props) {
        // title: str
        super(props);
    }

    render() {
        return (
            <div className="menu">
                <div className="title horizontal">
                    <div className="text">{this.props.title}</div>
                    <div className="icon">&#9654;</div>
                </div>
                <div className="content">{this.props.children}</div>
            </div>
        );
    }
}

Menu.propTypes = {
    title: PropTypes.string.isRequired
}
