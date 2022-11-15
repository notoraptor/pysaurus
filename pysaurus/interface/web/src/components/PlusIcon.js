import { MicroButton } from "./MicroButton.js";

export function PlusIcon(props) {
	return (
		<MicroButton
			type="plus"
			content={"\u271A"}
			title={props.title}
			action={props.action}
		/>
	);
}

PlusIcon.propTypes = {
	title: PropTypes.string,
	action: PropTypes.func,
};
