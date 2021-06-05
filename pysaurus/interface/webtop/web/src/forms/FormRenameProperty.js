import {Dialog} from "../dialogs/Dialog.js";

export class FormRenameProperty extends React.Component {
    constructor(props) {
        // title: str
        // onClose(newTitle)
        super(props);
        this.state = {title: this.props.title};
        this.onChange = this.onChange.bind(this);
        this.onClose = this.onClose.bind(this);
        this.onKeyDown = this.onKeyDown.bind(this);
        this.submit = this.submit.bind(this);
        this.onFocusInput = this.onFocusInput.bind(this);
    }

    render() {
        return (
            <Dialog title={`Rename property "${this.props.title}"?`} yes="rename" onClose={this.onClose}>
                <div className="form-rename-video">
                    <h1>Rename property</h1>
                    <h2><code id="filename">{this.props.title}</code></h2>
                    <p className="form">
                        <input type="text"
                               id="name"
                               value={this.state.title}
                               onChange={this.onChange}
                               onKeyDown={this.onKeyDown}
                               onFocus={this.onFocusInput}/>
                    </p>
                </div>
            </Dialog>
        )
    }

    componentDidMount() {
        document.querySelector('input#name').focus();
    }

    onFocusInput(event) {
        event.target.select();
    }

    onChange(event) {
        this.setState({title: event.target.value});
    }

    onClose(yes) {
        this.submit(yes);
    }

    onKeyDown(event) {
        if (event.key === "Enter") {
            Fancybox.close();
            this.submit(true);
        }
    }

    submit(yes) {
        let title = null;
        if (yes) {
            title = this.state.title;
            if (!title.length || title === this.props.title)
                title = null;
        }
        this.props.onClose(title);
    }
}
