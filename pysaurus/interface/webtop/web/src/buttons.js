export class Cross extends React.Component {
    constructor(props) {
        // action ? function()
        // title? str
        super(props);
        this.type = "cross";
        this.content = Utils.CHARACTER_CROSS;
    }
    render() {
        return (
            <div className={"small-button " + this.type}
                 {...(this.props.title ? {title: this.props.title} : {})}
                 {...(this.props.action ? {onClick: this.props.action} : {})}>
                {this.content}
            </div>
        );
    }
}

export class SettingIcon extends Cross {
    constructor(props) {
        // action ? function()
        // title? str
        super(props);
        this.type = "settings";
        this.content = Utils.CHARACTER_SETTINGS;
    }
}
