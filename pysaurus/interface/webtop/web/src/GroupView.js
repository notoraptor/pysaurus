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
            selection: new Set()
        };
        this.openPropertyOptions = this.openPropertyOptions.bind(this);
        this.openPropertyOptionsAll = this.openPropertyOptionsAll.bind(this);
        this.openPropertyPlus = this.openPropertyPlus.bind(this);
        this.setPage = this.setPage.bind(this);
        this.search = this.search.bind(this);
        this.allChecked = this.allChecked.bind(this);
        this.onCheckEntry = this.onCheckEntry.bind(this);
        this.onCheckAll = this.onCheckAll.bind(this);
        this.nullIndex = -1;
        for (let i = 0; i < this.props.groups.length; ++i) {
            if (this.props.groups[i].value === null) {
                if (i !== 0)
                    throw `Group without value at position ${i}, expected 0`;
                this.nullIndex = i;
                break;
            }
        }
    }
    render() {
        const selected = this.props.groupID;
        const isProperty = (this.props.field.charAt(0) === ':');
        const start = this.state.pageSize * this.state.pageNumber;
        const end = Math.min(start + this.state.pageSize, this.props.groups.length);
        const allChecked = this.allChecked(start, end);
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
                    {isProperty ? (
                        <div className="selection line">
                            <div className="column">
                                <input id="group-view-select-all"
                                       type="checkbox"
                                       checked={allChecked}
                                       onChange={event => this.onCheckAll(event, start, end)}/>
                                {' '}
                                <label htmlFor="group-view-select-all">
                                    {allChecked ? 'All ' : ''}{this.state.selection.size} selected
                                </label>
                                {this.state.selection.size ? (
                                    <span>
                                        &nbsp;
                                        <SettingIcon key="options-for-selected"
                                                     title={`Options for selected...`}
                                                     action={this.openPropertyOptionsAll}/>
                                    </span>) : ''}
                            </div>
                        </div>
                    ) : ''}
                </div>
                <div className="content">
                    {this.props.groups.slice(start, end).map((entry, index) => {
                        index = start + index;
                        const buttons = [];
                        if (isProperty && entry.value !== null) {
                            buttons.push(<input type="checkbox" checked={this.state.selection.has(index)} onChange={event => this.onCheckEntry(event, index)}/>)
                            buttons.push(' ');
                            if (this.props.onOptions && !this.state.selection.size) {
                                buttons.push(<SettingIcon key="options"
                                                          title={`Options ...`}
                                                          action={(event) => this.openPropertyOptions(event, index)}/>);
                                buttons.push(' ');
                            }
                            if (this.props.onPlus && !this.state.selection.size) {
                                buttons.push(<PlusIcon key="add"
                                                       title={`Add ...`}
                                                       action={(event) => this.openPropertyPlus(event, index)}/>);
                                buttons.push(' ');
                            }
                        }
                        return (
                            <div className={`line ${selected === index ? 'selected' : ''} ${isProperty ? 'property' : 'attribute'} ${entry.value === null ? 'all' : ''}`}
                                 key={index}
                                 onClick={() => this.select(index)}>
                                <div className="column left" {...(isProperty ? {} : {title: entry.value})}>
                                    {buttons}
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
        this.props.onOptions(new Set([index]));
    }
    openPropertyOptionsAll() {
        this.props.onOptions(this.state.selection);
    }
    openPropertyPlus(event, index) {
        event.cancelBubble = true;
        event.stopPropagation();
        this.props.onPlus(index);
    }
    setPage(pageNumber) {
        if (this.state.pageNumber !== pageNumber)
            this.setState({pageNumber: pageNumber, selection: new Set()});
    }
    search(text) {
        for (let index = 0; index < this.props.groups.length; ++index) {
            const value = this.props.groups[index].value;
            if (value === null)
                continue;
            if (value.toString().toLowerCase().indexOf(text.trim().toLowerCase()) !== 0)
                continue;
            const pageNumber = Math.floor(index / this.state.pageSize);
            if (this.state.pageNumber !== pageNumber)
               this.setState({pageNumber: pageNumber, selection: new Set()}, () => this.select(index));
            return;
        }
    }
    allChecked(start, end) {
        for (let i = start; i < end; ++i) {
            if (!this.state.selection.has(i) && i !== this.nullIndex)
                return false;
        }
        return true;
    }
    onCheckEntry(event, index) {
        const selection = new Set(this.state.selection);
        if (event.target.checked) {
            selection.add(index);
        } else {
            selection.delete(index);
        }
        this.setState({selection});
    }
    onCheckAll(event, start, end) {
        const selection = new Set(this.state.selection);
        if (event.target.checked) {
            for (let i = start; i < end; ++i) {
                selection.add(i);
            }
        } else {
            for (let i = start; i < end; ++i) {
                selection.delete(i);
            }
        }
        selection.delete(this.nullIndex);
        this.setState({selection});
    }
}