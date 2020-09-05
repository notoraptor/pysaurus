import {FIELD_TITLES} from "./constants.js";
import {SettingIcon, PlusIcon} from "./buttons.js";
import {Pagination} from "./Pagination.js";

export class GroupView extends React.Component {
    constructor(props) {
        /*
        groupID
        field
        sorting
        reverse
        groups
        onSelect(index)
        onOptions? callback(index)
        onPlus? callback(index)
        */
        super(props);
        this.state = {
            pageSize: 100,
            pageNumber: 0,
        };
        this.openPropertyOptions = this.openPropertyOptions.bind(this);
        this.setPage = this.setPage.bind(this);
        this.search = this.search.bind(this);
    }
    render() {
        const selected = this.props.groupID;
        const isProperty = (this.props.field.charAt(0) === ':');
        const start = this.state.pageSize * this.state.pageNumber;
        const end = Math.min(start + this.state.pageSize, this.props.groups.length);
        console.log(`Rendering ${this.props.groups.length} group(s).`);
        return (
            <div className="group-view">
                <div className="header">
                    <div className="title">{this.renderTitle()}</div>
                    <div>
                        <Pagination singular="page"
                                    plural="pages"
                                    nbPages={this.getNbPages()}
                                    pageNumber={this.state.pageNumber}
                                    onChange={this.setPage}
                                    onSearch={this.search}/>
                    </div>
                </div>
                <div className="content">
                    {this.props.groups.slice(start, end).map((entry, index) => {
                        index = start + index;
                        return (
                            <div className={`line ${selected === index ? 'selected' : ''} ${isProperty ? 'property' : 'attribute'} ${entry.value === null ? 'all' : ''}`}
                                 key={index}
                                 onClick={() => this.select(index)}>
                                <div className="column left" {...(isProperty ? {} : {title: entry.value})}>
                                    {isProperty && entry.value !== null ? ([
                                        this.props.onOptions ? (
                                            <SettingIcon key="options" title={`Options ...`} action={(event) => this.openPropertyOptions(event, index)}/>
                                        ) : (
                                            <PlusIcon key="add" title={`Add ...`} action={(event) => this.openPropertyOptions(event, index)}/>
                                        ),
                                        '  '
                                    ]) : ''}
                                    <span key="value" {...(isProperty ? {title: entry.value} : {})}>{entry.value === null ? `(none)` : entry.value}</span>
                                </div>
                                <div className="column right" title={entry.count}>{entry.count}</div>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    }
    renderTitle() {
        const field = this.props.field;
        let title = field.charAt(0) === ':' ?
            `"${Utils.sentence(field.substr(1))}"` :
            Utils.sentence(FIELD_TITLES[field]);
        if (this.props.sorting === "length")
            title = `|| ${title} ||`;
        else if (this.props.sorting === "count")
            title = `${title} (#)`;
        title = `${title} ${this.props.reverse ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}`;
        return title;
    }
    getNbPages() {
        const count = this.props.groups.length;
        return Math.floor(count / this.state.pageSize) + (count % this.state.pageSize ? 1 : 0);
    }
    select(value) {
        this.props.onSelect(value);
    }
    openPropertyOptions(event, index) {
        event.cancelBubble = true;
        event.stopPropagation();
        if (this.props.onPlus)
            this.props.onPlus(index);
        else if (this.props.onOptions)
            this.props.onOptions(index);
    }
    setPage(pageNumber) {
        this.setState({pageNumber});
    }
    search(text) {
        for (let index = 0; index < this.props.groups.length; ++index) {
            const value = this.props.groups[index].value;
            if (value === null)
                continue;
            if (value.toString().toLowerCase().indexOf(text.trim().toLowerCase()) !== 0)
                continue;
            const pageNumber = Math.floor(index / this.state.pageSize);
            this.setState({pageNumber}, () => this.select(index));
            return;
        }
    }
}
