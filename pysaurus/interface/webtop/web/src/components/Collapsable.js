export class Collapsable extends React.Component {
    constructor(props) {
        // title: str
        // className? str
        // children ...
        // lite? bool = true
        super(props);
        this.state = {stack: false};
        this.stack = this.stack.bind(this);
    }

    render() {
        const lite = this.props.lite !== undefined ? this.props.lite : true;
        return (
            <div className={`${lite ? "collapsable" : "stack"} ${this.props.className || {}}`}>
                <div className="header horizontal" onClick={this.stack}>
                    <div className="title">{this.props.title}</div>
                    <div className="icon">
                        {this.state.stack ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}
                    </div>
                </div>
                {this.state.stack ? '' : (
                    <div className="content">{this.props.children}</div>
                )}
            </div>
        );
    }

    stack() {
        this.setState({stack: !this.state.stack});
    }
}