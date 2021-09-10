export function Menu(props) {
    return (
        <div className="menu position-relative">
            <div className="title horizontal">
                <div className="text">{props.title}</div>
                <div className="icon">&#9654;</div>
            </div>
            <div className="content">{props.children}</div>
        </div>
    );
}
Menu.propTypes = {
    title: PropTypes.string.isRequired
}
