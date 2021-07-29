export class FancyBox extends React.Component {
    /**
     * @param props {{title: str}}
     */
    constructor(props) {
        // title, onClose() ?, children
        super(props);
        this.callbackIndex = -1;
        this.checkShortcut = this.checkShortcut.bind(this);
        this.onClose = this.onClose.bind(this);
    }

    render() {
        return (
            <div className="fancybox-wrapper absolute-plain">
                <div className="fancybox vertical">
                    <div className="fancybox-header horizontal">
                        <div className="fancybox-title">{this.props.title}</div>
                        <div className="fancybox-close">
                            <button onClick={this.onClose}>&times;</button>
                        </div>
                    </div>
                    <div className="fancybox-content">
                        {this.props.children}
                    </div>
                </div>
            </div>
        );
    }

    componentDidMount() {
        this.callbackIndex = KEYBOARD_MANAGER.register(this.checkShortcut);
    }

    componentWillUnmount() {
        KEYBOARD_MANAGER.unregister(this.callbackIndex);
    }

    /**
     * @param event {KeyboardEvent}
     */
    checkShortcut(event) {
        if (event.key === "Escape") {
            this.onClose();
            return true;
        }
    }

    onClose() {
        if (!this.props.onClose || this.props.onClose())
            Fancybox.close();
    }
}
FancyBox.propTypes = {
    title: PropTypes.string.isRequired,
    // onClose()
    onClose: PropTypes.func,
}
