export function Cell(props) {
    const classNames = ['cell-wrapper'];
    if (props.className)
        classNames.push(props.className);
    if (props.center) {
        classNames.push('cell-center');
        classNames.push('horizontal');
    }
    if (props.full)
        classNames.push('cell-full');
    return (
        <div className={classNames.join(' ')}>
            <div className="cell">
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