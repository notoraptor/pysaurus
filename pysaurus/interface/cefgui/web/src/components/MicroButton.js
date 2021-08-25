export function MicroButton(props) {
    return (
        <div className={"small-button " + props.type}
             {...(props.title ? {title: props.title} : {})}
             {...(props.action ? {onClick: props.action} : {})}>
            {props.content}
        </div>
    );
}
MicroButton.propTypes = {
    title: PropTypes.string,
    action: PropTypes.func,
    type: PropTypes.string.isRequired,
    content: PropTypes.string.isRequired
};
