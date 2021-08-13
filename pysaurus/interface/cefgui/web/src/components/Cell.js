export class Cell extends React.Component {
    // className? str
    // center? bool
    // full? bool
    render() {
        const classNames = ['cell-wrapper'];
        if (this.props.className)
            classNames.push(this.props.className);
        if (this.props.center) {
            classNames.push('cell-center');
            classNames.push('horizontal');
        }
        if (this.props.full)
            classNames.push('cell-full');
        return (
            <div className={classNames.join(' ')}>
                <div className="cell">
                    {this.props.children}
                </div>
            </div>
        );
    }
}
Cell.propTypes = {
    className: PropTypes.string,
    center: PropTypes.bool,
    full: PropTypes.bool,
}
