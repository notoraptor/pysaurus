import { Action } from "../utils/Action.js";
import { Cross } from "./Cross.js";

export function ActionToCross(props) {
	const { action, title } = props;
	return <Cross title={`${title || action.title} (${action.shortcut.str})`} action={action.callback} />;
}

ActionToCross.propTypes = {
	action: PropTypes.instanceOf(Action),
	title: PropTypes.string,
};
