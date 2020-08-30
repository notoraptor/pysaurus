import {FIELD_TITLES} from "./constants.js";
import {SettingIcon} from "./buttons.js";
import {Pagination} from "./Pagination.js";

export class GroupView extends React.Component {
    constructor(props) {
        // definition: GroupDef
        // onSelect
        // onValueOptions(name, value)
        super(props);
        this.state = {
            pageSize: 100,
            pageNumber: 0,
        };
        this.openPropertyOptions = this.openPropertyOptions.bind(this);
        this.setPage = this.setPage.bind(this);
    }
    getNbPages() {
        const count = this.props.definition.groups.length;
        return Math.floor(count / this.state.pageSize) + (count % this.state.pageSize ? 1 : 0);
    }
    renderTitle() {
        const field = this.props.definition.field;
        let title = field.charAt(0) === ':' ?
            `"${Utils.sentence(field.substr(1))}"`
            : Utils.sentence(FIELD_TITLES[this.props.definition.field]);
        if (this.props.definition.sorting === "length")
            title = `|| ${title} ||`;
        else if (this.props.definition.sorting === "count")
            title = `${title} (#)`;
        title = `${title} ${this.props.definition.reverse ? Utils.CHARACTER_ARROW_DOWN : Utils.CHARACTER_ARROW_UP}`;
        return title;
    }
    render() {
        const selected = this.props.definition.group_id;
        const isProperty = (this.props.definition.field.charAt(0) === ':');
        const start = this.state.pageSize * this.state.pageNumber;
        const end = Math.min(start + this.state.pageSize, this.props.definition.groups.length);
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
                        />
                    </div>
                </div>
                <div className="content">
                    {this.props.definition.groups.slice(start, end).map((entry, index) => (
                        <div className={`line ${selected === index ? 'selected' : ''} ${isProperty ? 'property' : 'attribute'}`}
                             key={index}
                             onClick={() => this.select(start + index)}>
                            <div className="column left" {...(isProperty ? {} : {title: entry.value})}>
                                {isProperty ? ([<SettingIcon key="options" title={`Options ...`} action={() => this.openPropertyOptions(index)}/>, '  ']) : ''}
                                <span key="value" {...(isProperty ? {title: entry.value} : {})}>{entry.value}</span>
                            </div>
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
    openPropertyOptions(index) {
        this.props.onValueOptions(
            this.props.definition.field.substr(1),
            this.props.definition.groups[index].value
        );
    }
    setPage(pageNumber) {
        this.setState({pageNumber});
    }
}
