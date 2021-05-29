import {Cross} from "./Cross.js";

/**
 * @param props {{action: Action, title: str?}}
 */
export function ActionToCross(props) {
    const {action, title} = props;
    return <Cross title={`${title || action.title} (${action.shortcut.str})`} action={action.callback}/>;
}