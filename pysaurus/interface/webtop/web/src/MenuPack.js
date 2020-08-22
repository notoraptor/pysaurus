export class MenuPack extends React.Component {
    constructor(props) {
        // title: str
        super(props);
    }
    render() {
        return (
            <div className="menu-pack">
                <div className="title" onClick={this.showMenu}>
                    <div className="text">
                        {this.props.title}
                    </div>
                </div>
                <div className="content">{this.props.children}</div>
            </div>
        );
    }
}

export class MenuItem extends React.Component {
    constructor(props) {
        // className? str
        // shortcut? str
        // action? function()
        super(props);
        this.onClick = this.onClick.bind(this);
    }
    render() {
        const classNames = ["menu-item horizontal"];
        if (this.props.className)
            classNames.push(this.props.className);
        return (
            <div className={classNames.join(' ')} onClick={this.onClick}>
                <div className="icon"/>
                <div className="text horizontal">
                    <div className="title">{this.props.children}</div>
                    <div className="shortcut">{this.props.shortcut || ''}</div>
                </div>
            </div>
        );
    }
    onClick() {
        if (this.props.action)
            this.props.action();
    }
}

export class MenuItemCheck extends React.Component {
    constructor(props) {
        // action? function(checked)
        // checked? bool
        super(props);
        this.onClick = this.onClick.bind(this);
    }
    render() {
        const checked = !!this.props.checked;
        return (
            <div className="menu-item horizontal" onClick={this.onClick}>
                <div className="icon">
                    <div className="border">
                        <div className={'check ' + (checked ? 'checked' : 'not-checked')}/>
                    </div>
                </div>
                <div className="text">{this.props.children}</div>
            </div>
        );
    }
    onClick() {
        const checked = !this.props.checked;
        if (this.props.action)
            this.props.action(checked);
    }
}

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
