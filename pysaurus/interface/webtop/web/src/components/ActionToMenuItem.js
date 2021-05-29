import {MenuItem} from "./MenuItem.js";

/**
 * @param props {{action: Action, title: str?}}
 */
export function ActionToMenuItem(props) {
    const {action, title} = props;
    return <MenuItem shortcut={action.shortcut.str} action={action.callback}>{title || action.title}</MenuItem>;
}