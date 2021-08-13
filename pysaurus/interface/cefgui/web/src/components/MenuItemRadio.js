/**
 * @callback MenuItemRadioCallback
 * @param {Object} value
 */

/**
 * @param props {{value: Object, checked: boolean, action: MenuItemRadioCallback, children: Object}}
 */
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
