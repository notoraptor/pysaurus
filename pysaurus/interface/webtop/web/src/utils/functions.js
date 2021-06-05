/**
 * @param propType {string}
 * @param propEnum {Array}
 * @param value {string}
 * @returns {null}
 */
export function parsePropValString(propType, propEnum, value) {
    let parsed = null;
    switch (propType) {
        case "bool":
            if (value === "false")
                parsed = false;
            else if (value === "true")
                parsed = true;
            else
                throw `Invalid bool value, expected: [false, true], got ${value}`;
            break;
        case "int":
            parsed = parseInt(value);
            if (isNaN(parsed))
                throw `Unable to parse integer: ${value}`;
            break;
        case "float":
            parsed = parseFloat(value);
            if (isNaN(parsed))
                throw `Unable to parse floating value: ${value}`;
            break;
        case "str":
            parsed = value;
            break;
        default:
            throw `Unknown property type: ${propType}`;
    }
    if (propEnum && propEnum.indexOf(parsed) < 0)
        throw `Invalid enum value, expected: [${propEnum.join(', ')}], got ${value}`;
    return parsed;
}

export function capitalizeFirstLetter(str) {
    if (str.length === 0)
        return str;
    if (str.length === 1)
        return str.toUpperCase();
    return str.substr(0, 1).toUpperCase() + str.substr(1);
}
