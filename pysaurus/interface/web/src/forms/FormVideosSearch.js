import {FancyBox} from "../dialogs/FancyBox.js";

export class FormVideosSearch extends React.Component {
    constructor(props) {
        // text
        // cond
        // onClose(criterion)
        super(props);
        this.state = {
            text: this.props.text || "",
            cond: this.props.cond || "",
        }
        this.onFocusInput = this.onFocusInput.bind(this);
        this.onChangeInput = this.onChangeInput.bind(this);
        this.onChangeCond = this.onChangeCond.bind(this);
        this.onInput = this.onInput.bind(this);
        this.onClose = this.onClose.bind(this);
    }

    render() {
        return (
            <FancyBox title={PYTHON_LANG.form_title_search_videos}>
                <div className="form-videos-search text-center">
                    {PYTHON_LANG.form_content_search_videos.markdown()}
                    <p>
                        <input type="text"
                               id="input-search"
                               className="block mb-2"
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
                        <label htmlFor="input-search-and">{PYTHON_LANG.search_and}</label>
                    </p>
                    <p>
                        <input type="radio"
                               id="input-search-or"
                               name="searchType"
                               value="or"
                               onChange={this.onChangeCond}
                               checked={this.state.cond === 'or'}/>
                        <label htmlFor="input-search-or">{PYTHON_LANG.search_or}</label>
                    </p>
                    <p>
                        <input type="radio"
                               id="input-search-exact"
                               name="searchType"
                               value="exact"
                               onChange={this.onChangeCond}
                               checked={this.state.cond === 'exact'}/>
                        <label htmlFor="input-search-exact">{PYTHON_LANG.search_exact_sentence}</label>
                    </p>
                    <p>
                        <input type="radio"
                               id="input-search-id"
                               name="searchType"
                               value="id"
                               onChange={this.onChangeCond}
                               checked={this.state.cond === 'id'}/>
                        <label htmlFor="input-search-id">{PYTHON_LANG.search_id}</label>
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
        this.setState({text: event.target.value, cond: ""});
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
