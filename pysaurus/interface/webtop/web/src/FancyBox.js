export class FancyBox extends React.Component {
    constructor(props) {
        // title
        // onClose()
        // onBuild(onClose)
        super(props);
        this.callbackIndex = -1;
        this.checkShortcut = this.checkShortcut.bind(this);
    }
    render() {
        return (
            <div className="fancybox-wrapper">
                <div className="fancybox">
                    <div className="fancybox-header horizontal">
                        <div className="fancybox-title">{this.props.title}</div>
                        <div className="fancybox-close"><button onClick={this.props.onClose}>&times;</button></div>
                    </div>
                    <div className="fancybox-content">
                        <div className="fancybox-inner-content">{this.props.onBuild(this.props.onClose)}</div>
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
            this.props.onClose();
            return true;
        }
    }
}
