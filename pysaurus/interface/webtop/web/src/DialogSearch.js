import {Cell} from "./Cell.js";
import {Dialog} from "./Dialog.js";

export class DialogSearch extends React.Component {
    constructor(props) {
        // onClose(criterion)
        super(props);
        this.state = {
            text: '',
        }
        this.onFocusInput = this.onFocusInput.bind(this);
        this.onChangeInput = this.onChangeInput.bind(this);
        this.onInput = this.onInput.bind(this);
        this.onClose = this.onClose.bind(this);
    }
    render() {
        return (
            <Dialog yes={"go"} no={"cancel"} onClose={this.onClose}>
                <Cell center={true} full={true} className="text-center">
                    <input type="text"
                           id="input-search"
                           placeholder="Search ..."
                           onFocus={this.onFocusInput}
                           onChange={this.onChangeInput}
                           onKeyDown={this.onInput}
                           value={this.state.text}/>
                </Cell>
            </Dialog>
        );
    }
    componentDidMount() {
        document.querySelector('#input-search').focus();
    }
    onFocusInput(event) {
        event.target.select();
    }
    onChangeInput(event) {
        this.setState({text: event.target.value});
    }
    onInput(event) {
        if (event.key === "Enter" && this.state.text.length) {
            this.props.onClose(this.state.text);
            return true;
        }
    }
    onClose(yes) {
        this.props.onClose(yes && this.state.text ? this.state.text : null);
    }
}