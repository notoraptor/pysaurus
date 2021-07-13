import {FancyBox} from "./FancyBox.js";

export class Dialog extends React.Component {
    constructor(props) {
        super(props);
        this.yes = this.yes.bind(this);
    }

    render() {
        return (
            <FancyBox title={this.props.title}>
                <div className="dialog absolute-plain vertical">
                    <div className="content vertical">{this.props.children}</div>
                    <div className="buttons horizontal">
                        <div className="button yes">
                            <button onClick={this.yes}>{this.props.yes || "yes"}</button>
                        </div>
                        <div className="button no">
                            <button onClick={Fancybox.close}>{this.props.no || "cancel"}</button>
                        </div>
                    </div>
                </div>
            </FancyBox>
        );
    }

    yes() {
        Fancybox.close();
        if (this.props.action)
            this.props.action();
    }
}

Dialog.propTypes = {
    title: PropTypes.string.isRequired,
    // action()
    action: PropTypes.func,
    yes: PropTypes.string,
    no: PropTypes.string
}
