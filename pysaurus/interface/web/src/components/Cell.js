export function Cell(props) {
    const classNames = [];
    if (props.className)
        classNames.push(props.className);
    if (props.center) {
        classNames.push('cell-center');
        classNames.push('horizontal');
    }
    if (props.full) {
        classNames.push('position-relative');
        classNames.push("w-100");
        classNames.push("h-100");
        classNames.push("flex-grow-1");
    }
    return (
        <div className={classNames.join(' ')}>
            <div className="w-100">
                {props.children}
            </div>
        </div>
    );
}
Cell.propTypes = {
    className: PropTypes.string,
    center: PropTypes.bool,
    full: PropTypes.bool,
}
