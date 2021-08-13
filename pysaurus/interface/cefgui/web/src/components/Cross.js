import {Characters} from "../utils/constants.js";

export class Cross extends React.Component {
    constructor(props) {
        // action ? function()
        // title? str
        super(props);
        this.type = "cross";
        this.content = Characters.CROSS;
    }

    render() {
        return (
            <div className={"small-button " + this.type}
                 {...(this.props.title ? {title: this.props.title} : {})}
                 {...(this.props.action ? {onClick: this.props.action} : {})}>
                {this.content}
            </div>
        );
    }
}