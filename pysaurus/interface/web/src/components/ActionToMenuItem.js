import {MenuItem} from "./MenuItem.js";
import {Action} from "../utils/Action.js";

export function ActionToMenuItem(props) {
    const {action, title} = props;
    return <MenuItem shortcut={action.shortcut.str} action={action.callback}>{title || action.title}</MenuItem>;
}

ActionToMenuItem.propTypes = {
    action: PropTypes.instanceOf(Action).isRequired,
    title: PropTypes.string
}
