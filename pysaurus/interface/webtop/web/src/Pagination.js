export class Pagination extends React.Component {
    constructor(props) {
        // singular: str
        // plural: str
        // nbPages: int
        // pageNumber: int
        // onChange: function(int)
        super(props);
        this.onFirst = this.onFirst.bind(this);
        this.onNext = this.onNext.bind(this);
        this.onLast = this.onLast.bind(this);
        this.onPrevious = this.onPrevious.bind(this);
        this.onInput = this.onInput.bind(this);
    }
    render() {
        const singular = this.props.singular;
        const plural = this.props.plural;
        const nbPages = this.props.nbPages;
        const pageNumber = this.props.pageNumber;
        const nbCharacters = Math.round(Math.log10(nbPages)) + 1;
        return (
            nbPages ? (
                <span className="navigation">
                    <button className="first" disabled={pageNumber === 0} onClick={this.onFirst}>&lt;&lt;</button>
                    <button className="previous" disabled={pageNumber === 0} onClick={this.onPrevious}>&lt;</button>{' '}
                    <span>
                        {Utils.sentence(singular)}{' '}
                        <input type="number"
                               className="current"
                               style={{width: `${nbCharacters}em`}}
                               min={1}
                               max={nbPages}
                               step={1}
                               value={pageNumber + 1}
                               onChange={this.onInput}/> / {nbPages}
                    </span>{' '}
                    <button className="next" disabled={pageNumber === nbPages - 1} onClick={this.onNext}>&gt;</button>
                    <button className="last" disabled={pageNumber === nbPages - 1} onClick={this.onLast}>&gt;&gt;</button>
                </span>
            ) : (<div className="navigation status"><em>0 {plural}</em></div>)
        )
    }

    onFirst() {
        if (this.props.pageNumber !== 0) {
            this.props.onChange(0);
        }
    }
    onPrevious() {
        if (this.props.pageNumber > 0) {
            this.props.onChange(this.props.pageNumber - 1);
        }
    }
    onNext() {
        if (this.props.pageNumber < this.props.nbPages - 1) {
            this.props.onChange(this.props.pageNumber + 1);
        }
    }
    onLast() {
        if (this.props.pageNumber !== this.props.nbPages - 1) {
            this.props.onChange(this.props.nbPages - 1);
        }
    }
    onInput(event) {
        const value = event.target.value;
        let pageNumber = (value || 1) - 1;
        if (pageNumber >= this.props.nbPages)
            pageNumber = this.props.nbPages - 1;
        if (pageNumber < 0)
            pageNumber = 0;
        if (pageNumber !== this.props.pageNumber)
            this.props.onChange(pageNumber);
    }
}