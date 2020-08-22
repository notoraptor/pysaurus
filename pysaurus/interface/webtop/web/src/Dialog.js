export class Dialog extends React.Component {
    constructor(props) {
        // onClose: callback(bool)
        // yes? str
        // no? str
        super(props);
        this.yes = this.yes.bind(this);
        this.no = this.no.bind(this);
    }
    render() {
        return (
            <div className="dialog">
                <div className="content">
                    <div className="wrapper">
                        {this.props.children}
                    </div>
                </div>
                <div className="buttons horizontal">
                    <div className="button yes"><button onClick={this.yes}>{this.props.yes || "yes"}</button></div>
                    <div className="button no"><button onClick={this.no}>{this.props.no || "no"}</button></div>
                </div>
            </div>
        );
    }
    yes() {
        this.props.onClose(true);
    }
    no() {
        this.props.onClose(false);
    }
}