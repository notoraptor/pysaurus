export function MicroButton(props) {
    return (
        <div className={"small-button clickable bold text-center " + props.type}
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
