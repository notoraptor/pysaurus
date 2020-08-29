import {FIELD_TITLES} from "./constants.js";

function applyReverse(value, reverse) {
    return reverse ? -value: value;
}

function compareString(a, b) {
    let t = a.toLowerCase().localeCompare(b.toLowerCase());
    if (t === 0)
        t = a.localeCompare(b);
    return t;
}

function compareEntryCount(entry1, entry2, reverse) {
    let t = applyReverse(entry1[1] - entry2[1], reverse);
    if (t === 0)
        t = compareString(entry1[0], entry2[0]);
    return t;
}

function compareEntryField(entry1, entry2, reverse) {
    let t = applyReverse(compareString(entry1[0], entry2[0]), reverse);
    if (t === 0)
        t = entry1[1] - entry2[1];
    return t;
}

function compareEntryFieldLength(entry1, entry2, reverse) {
    let t = applyReverse(entry1[0].length - entry2[0].length, reverse);
    if (t === 0)
        t = compareEntryField(entry1, entry2, reverse);
    return t;
}

const Comparison = {
    field: compareEntryField,
    length: compareEntryFieldLength,
    count: compareEntryCount
}

export class GroupView extends React.Component {
    constructor(props) {
        // definition: GroupDef
        // onSelect
        super(props);
    }
    renderTitle() {
        let title = Utils.sentence(FIELD_TITLES[this.props.definition.field]);
        if (this.props.definition.sorting === "length")
            title = `|| ${title} ||`;
        else if (this.props.definition.sorting === "count")
            title = `${title} (#)`;
        title = `${title} ${this.props.definition.reverse ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}`;
        return title;
    }
    render() {
        const selected = this.props.definition.group_id;
        return (
            <div className="group-view">
                <div className="header">
                    <div className="title">{this.renderTitle()}</div>
                </div>
                <div className="content">
                    {this.props.definition.groups.map((entry, index) => (
                        <div className={`line ${selected === index ? 'selected' : ''}`} key={index} onClick={() => this.select(index)}>
                            <div className="column left" title={entry.value}>{entry.value}</div>
                            <div className="column right" title={entry.count}>{entry.count}</div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    select(value) {
        this.props.onSelect(value);
    }
}
