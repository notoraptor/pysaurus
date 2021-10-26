export function MenuItemRadio(props) {
    return (
        <div className="menu-item radio horizontal" onClick={() => props.action(props.value)}>
            <div className="icon">
                <div className="border">
                    <div className={'check ' + (!!props.checked ? 'checked' : 'not-checked')}/>
                </div>
            </div>
            <div className="text">{props.children}</div>
        </div>
    );
}

MenuItemRadio.propTypes = {
    value: PropTypes.object,
    checked: PropTypes.bool,
    // action(value)
    action: PropTypes.func,
}
