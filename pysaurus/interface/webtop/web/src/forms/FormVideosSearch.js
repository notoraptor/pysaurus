import {FancyBox} from "../dialogs/FancyBox.js";

export class FormVideosSearch extends React.Component {
    constructor(props) {
        // text
        // cond
        // onClose(criterion)
        super(props);
        this.state = {
            text: this.props.text || '',
            cond: this.props.cond || '',
        }
        this.onFocusInput = this.onFocusInput.bind(this);
        this.onChangeInput = this.onChangeInput.bind(this);
        this.onChangeCond = this.onChangeCond.bind(this);
        this.onInput = this.onInput.bind(this);
        this.onClose = this.onClose.bind(this);
    }

    render() {
        return (
            <FancyBox title="Search videos">
                <div className="form-search">
                    <p>Type text to search and choose how to search.</p>
                    <p>You can also type text and then press enter to automatically select "AND" as search method.</p>
                    <p>
                        <input type="text"
                               id="input-search"
                               name="searchText"
                               placeholder="Search ..."
                               onFocus={this.onFocusInput}
                               onChange={this.onChangeInput}
                               onKeyDown={this.onInput}
                               value={this.state.text}/>
                    </p>
                    <p>
                        <input type="radio"
                               id="input-search-and"
                               name="searchType"
                               value="and"
                               onChange={this.onChangeCond}
                               checked={this.state.cond === 'and'}/>
                        <label htmlFor="input-search-and">all terms</label>
                    </p>
                    <p>
                        <input type="radio"
                               id="input-search-or"
                               name="searchType"
                               value="or"
                               onChange={this.onChangeCond}
                               checked={this.state.cond === 'or'}/>
                        <label htmlFor="input-search-or">any term</label>
                    </p>
                    <p>
                        <input type="radio"
                               id="input-search-exact"
                               name="searchType"
                               value="exact"
                               onChange={this.onChangeCond}
                               checked={this.state.cond === 'exact'}/>
                        <label htmlFor="input-search-exact">exact sentence</label>
                    </p>
                </div>
            </FancyBox>
        );
    }

    componentDidMount() {
        document.querySelector('#input-search').focus();
    }

    onFocusInput(event) {
        event.target.select();
    }

    onChangeInput(event) {
        this.setState({text: event.target.value, cond: ''});
    }

    onChangeCond(event) {
        const text = this.state.text;
        const cond = event.target.value;
        this.setState({text, cond}, () => {
            if (text.length && cond.length)
                this.onClose({text, cond});
        });
    }

    onInput(event) {
        if (event.key === "Enter") {
            if (this.state.text.length) {
                const text = this.state.text;
                const cond = 'and';
                this.onClose({text, cond});
                return true;
            }
        }
    }

    onClose(criterion) {
        Fancybox.close();
        this.props.onClose(criterion);
    }
}
