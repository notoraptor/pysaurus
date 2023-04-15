import { Action } from "../utils/Action.js";
import { SettingIcon } from "./SettingIcon.js";

export function ActionToSettingIcon(props) {
	const { action, title } = props;
	return <SettingIcon title={`${title || action.title} (${action.shortcut.str})`} action={action.callback} />;
}

ActionToSettingIcon.propTypes = {
	action: PropTypes.instanceOf(Action),
	title: PropTypes.string,
};
