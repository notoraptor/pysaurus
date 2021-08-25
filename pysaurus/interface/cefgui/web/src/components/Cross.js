import {Characters} from "../utils/constants.js";
import {MicroButton} from "./MicroButton.js";

export function Cross(props) {
    return <MicroButton type="cross" content={Characters.CROSS} title={props.title} action={props.action}/>;
}
Cross.propTypes = {
    title: PropTypes.string,
    action: PropTypes.func
};
