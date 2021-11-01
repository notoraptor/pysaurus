import {Dialog} from "../dialogs/Dialog.js";
import {LangContext} from "../language.js";

export class FormVideoRename extends React.Component {
    constructor(props) {
        // filename: str
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
            <Dialog title={"Rename"} yes="rename" action={this.onClose}>
                <div className="form-rename text-center">
                    <h1>{this.context.action_rename_video}</h1>
                    <h2><code id="filename">{this.props.filename}</code></h2>
                    <p className="form">
                        <input type="text"
                               id="name"
                               className="block"
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

    onClose() {
        this.submit();
    }

    onKeyDown(event) {
        if (event.key === "Enter") {
            Fancybox.close();
            this.submit();
        }
    }

    submit(yes) {
        if (this.state.title && this.state.title !== this.props.title)
            this.props.onClose(this.state.title);
    }
}
FormVideoRename.contextType = LangContext;
