import { Characters } from "../utils/constants.js";
import { MicroButton } from "./MicroButton.js";

export function SettingIcon(props) {
	return <MicroButton type="settings" content={Characters.SETTINGS} title={props.title} action={props.action} />;
}

SettingIcon.propTypes = {
	title: PropTypes.string,
	action: PropTypes.func,
};
