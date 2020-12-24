export class Stackable extends React.Component {
    constructor(props) {
        // title: str
        // className: str
        // children ...
        super(props);
        this.state = {stack: false};
        this.stack = this.stack.bind(this);
    }
    render() {
        return (
            <div className={`stack ${this.props.className || ''}`}>
                <div className="stack-title" onClick={this.stack}>
                    <div className="title">{this.props.title}</div>
                    <div className="icon">{this.state.stack ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}</div>
                </div>
                {this.state.stack ? '' : (
                    <div className="stack-content">{this.props.children}</div>
                )}
            </div>
        );
    }
    stack() {
        this.setState({stack: !this.state.stack});
    }
}