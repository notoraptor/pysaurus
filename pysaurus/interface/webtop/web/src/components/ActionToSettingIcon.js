import {SettingIcon} from "./SettingIcon.js";

/**
 * @param props {{action: Action, title: str?}}
 */
export function ActionToSettingIcon(props) {
    const {action, title} = props;
    return <SettingIcon title={`${title || action.title} (${action.shortcut.str})`} action={action.callback}/>;
}