import {Characters, FIELD_MAP} from "../utils/constants.js";
import {Pagination} from "./Pagination.js";
import {SettingIcon} from "./SettingIcon.js";
import {PlusIcon} from "./PlusIcon.js";
import {capitalizeFirstLetter} from "../utils/functions.js";
import {Actions} from "../utils/Actions.js";
import {Action} from "../utils/Action.js";

export class GroupView extends React.Component {
    constructor(props) {
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
        this.previousGroup = this.previousGroup.bind(this);
        this.nextGroup = this.nextGroup.bind(this);
        this.search = this.search.bind(this);
        this.allChecked = this.allChecked.bind(this);
        this.onCheckEntry = this.onCheckEntry.bind(this);
        this.onCheckAll = this.onCheckAll.bind(this);
        this.nullIndex = -1;
        for (let i = 0; i < this.props.groupDef.groups.length; ++i) {
            if (this.props.groupDef.groups[i].value === null) {
                if (i !== 0)
                    throw `Group without value at position ${i}, expected 0`;
                this.nullIndex = i;
                break;
            }
        }
        this.callbackIndex = -1;
        this.features = new Actions({
            previous: new Action("Ctrl+ArrowUp", "Go to previous group", this.previousGroup),
            next: new Action("Ctrl+ArrowDown", "Go to next group", this.nextGroup)
        });
    }

    render() {
        const selected = this.props.groupDef.group_id;
        const isProperty = this.props.groupDef.is_property;
        const start = this.state.pageSize * this.state.pageNumber;
        const end = Math.min(start + this.state.pageSize, this.props.groupDef.groups.length);
        const allChecked = this.allChecked(start, end);
        console.log(`Rendering ${this.props.groupDef.groups.length} group(s).`);
        return (
            <div className="group-view vertical">
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
                    {isProperty && !this.props.isClassified ? (
                        <div className="selection line horizontal">
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
                    {this.props.groupDef.groups.length ? (
                        <table className="second-td-text-right">
                            {this.props.groupDef.groups.slice(start, end).map((entry, index) => {
                                index = start + index;
                                const buttons = [];
                                if (isProperty && entry.value !== null) {
                                    if (!this.props.isClassified) {
                                        buttons.push(<input type="checkbox" checked={this.state.selection.has(index)}
                                                            onChange={event => this.onCheckEntry(event, index)}/>)
                                        buttons.push(' ');
                                        if (!this.state.selection.size) {
                                            buttons.push(<SettingIcon key="options"
                                                                      title={`Options ...`}
                                                                      action={(event) => this.openPropertyOptions(event, index)}/>);
                                            buttons.push(' ');
                                        }
                                    }
                                    if (!this.state.selection.size) {
                                        buttons.push(<PlusIcon key="add"
                                                               title={`Add ...`}
                                                               action={(event) => this.openPropertyPlus(event, index)}/>);
                                        buttons.push(' ');
                                    }
                                }
                                const classes = [isProperty ? "property" : "attribute"];
                                if (selected === index)
                                    classes.push("selected");
                                if (entry.value === null)
                                    classes.push("all");
                                return (
                                    <tr className={classes.join(" ")}
                                        key={index}
                                        onClick={() => this.props.onSelect(index)}>
                                        <td {...(isProperty ? {} : {title: entry.value})}>
                                            {buttons}
                                            <span key="value" {...(isProperty ? {title: entry.value} : {})}>
                                                {entry.value === null ? `(none)` : entry.value}
                                            </span>
                                        </td>
                                        <td title={entry.count}>{entry.count}</td>
                                    </tr>
                                );
                            })}
                        </table>
                    ) : <div className="absolute-plain no-groups vertical"><strong><em>No groups</em></strong></div>}
                </div>
            </div>
        );
    }

    renderTitle() {
        const field = this.props.groupDef.field;
        let title = this.props.groupDef.is_property ?
            `"${capitalizeFirstLetter(field)}"` : capitalizeFirstLetter(FIELD_MAP.fields[field].title);
        if (this.props.groupDef.sorting === "length")
            title = `|| ${title} ||`;
        else if (this.props.groupDef.sorting === "count")
            title = `${title} (#)`;
        title = `${title} ${this.props.groupDef.reverse ? Characters.ARROW_DOWN : Characters.ARROW_UP}`;
        return title;
    }

    componentDidMount() {
        this.callbackIndex = KEYBOARD_MANAGER.register(this.features.onKeyPressed);
    }

    componentWillUnmount() {
        KEYBOARD_MANAGER.unregister(this.callbackIndex);
    }

    getNbPages() {
        const count = this.props.groupDef.groups.length;
        return Math.floor(count / this.state.pageSize) + (count % this.state.pageSize ? 1 : 0);
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
        if (this.props.onPlus)
            this.props.onPlus(index);
    }

    setPage(pageNumber) {
        if (this.state.pageNumber !== pageNumber)
            this.setState({pageNumber: pageNumber, selection: new Set()});
    }

    previousGroup() {
        const groupID = this.props.groupDef.group_id;
        if (groupID > 0)
            this.props.onSelect(groupID - 1);
    }

    nextGroup() {
        const groupID = this.props.groupDef.group_id;
        if (groupID < this.props.groupDef.groups.length - 1)
            this.props.onSelect(groupID + 1);
    }

    search(text) {
        for (let index = 0; index < this.props.groupDef.groups.length; ++index) {
            const value = this.props.groupDef.groups[index].value;
            if (value === null)
                continue;
            if (value.toString().toLowerCase().indexOf(text.trim().toLowerCase()) !== 0)
                continue;
            const pageNumber = Math.floor(index / this.state.pageSize);
            if (this.state.pageNumber !== pageNumber)
                this.setState({pageNumber: pageNumber, selection: new Set()}, () => this.props.onSelect(index));
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

GroupView.propTypes = {
    groupDef: PropTypes.shape({
        group_id: PropTypes.number.isRequired,
        field: PropTypes.string.isRequired,
        is_property: PropTypes.bool.isRequired,
        sorting: PropTypes.string.isRequired,
        reverse: PropTypes.bool.isRequired,
        groups: PropTypes.arrayOf(PropTypes.shape({value: PropTypes.any, count: PropTypes.number})).isRequired
    }).isRequired,
    isClassified: PropTypes.bool.isRequired,
    // onSelect(index)
    onSelect: PropTypes.func.isRequired,
    // onOptions(index)
    onOptions: PropTypes.func.isRequired,
    // onPlus(index)
    onPlus: PropTypes.func,
}
