import {FancyBox} from "./FancyBox.js";

export class Dialog extends React.Component {
    /**
     * @param props {{title: string, onClose: function?, yes: string?, no: string?}}
     */
    constructor(props) {
        // title: str
        // onClose: callback(bool)
        // yes? str
        // no? str
        super(props);
        this.yes = this.yes.bind(this);
        this.no = this.no.bind(this);
    }

    render() {
        return (
            <FancyBox title={this.props.title}>
                <div className="dialog">
                    <div className="content">{this.props.children}</div>
                    <div className="buttons horizontal">
                        <div className="button yes">
                            <button onClick={this.yes}>{this.props.yes || "yes"}</button>
                        </div>
                        <div className="button no">
                            <button onClick={this.no}>{this.props.no || "cancel"}</button>
                        </div>
                    </div>
                </div>
            </FancyBox>
        );
    }

    yes() {
        Fancybox.onClose();
        if (this.props.onClose)
            this.props.onClose(true);
    }

    no() {
        Fancybox.onClose();
        if (this.props.onClose)
            this.props.onClose(false);
    }
}