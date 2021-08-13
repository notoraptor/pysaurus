import {Dialog} from "../dialogs/Dialog.js";
import {Cell} from "../components/Cell.js";

export class FormPaginationGoTo extends React.Component {
    constructor(props) {
        // nbPages
        // pageNumber
        // onClose(pageNumber)
        super(props);
        this.state = {pageNumber: this.props.pageNumber};
        this.onFocusInput = this.onFocusInput.bind(this);
        this.onChange = this.onChange.bind(this);
        this.onInput = this.onInput.bind(this);
        this.onClose = this.onClose.bind(this);
    }

    render() {
        return (
            <Dialog title={"Go to page:"} yes={"go"} action={this.onClose}>
                <Cell center={true} full={true} className="text-center">
                    <input type="number"
                           id="input-go"
                           min={1}
                           max={this.props.nbPages}
                           step={1}
                           value={this.state.pageNumber + 1}
                           onFocus={this.onFocusInput}
                           onChange={this.onChange}
                           onKeyDown={this.onInput}/> / {this.props.nbPages}
                </Cell>
            </Dialog>
        );
    }

    componentDidMount() {
        document.querySelector('#input-go').focus();
    }

    onFocusInput(event) {
        event.target.select();
    }

    onChange(event) {
        const value = event.target.value;
        let pageNumber = (value || 1) - 1;
        if (pageNumber >= this.props.nbPages)
            pageNumber = this.props.nbPages - 1;
        if (pageNumber < 0)
            pageNumber = 0;
        this.setState({pageNumber});
    }

    onInput(event) {
        if (event.key === "Enter") {
            Fancybox.close();
            this.props.onClose(this.state.pageNumber);
        }
    }

    onClose() {
        this.props.onClose(this.state.pageNumber);
    }
}
