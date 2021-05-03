export class MenuPack extends React.Component {
    constructor(props) {
        // title: str
        super(props);
    }
    render() {
        return (
            <div className="menu-pack">
                <div className="title">
                    <div className="text">
                        {this.props.title}
                    </div>
                </div>
                <div className="content">{this.props.children}</div>
            </div>
        );
    }
}
