export function capitalizeFirstLetter(str) {
    if (str.length === 0)
        return str;
    if (str.length === 1)
        return str.toUpperCase();
    return str.substr(0, 1).toUpperCase() + str.substr(1);
}

/**
 *
 * @param text {string}
 * @param kwargs {Object}
 * @return string
 */
export function formatString(text, kwargs) {
    for (let entry of Object.entries(kwargs)) {
        const [key, value] = entry;
        text = text.replace(new RegExp("\\{" + key + "\\}", "g"), value.toString());
    }
    return text;
}

export class IdGenerator {
    constructor() {
        this.id = 0;
    }

    next() {
        return ++this.id;
    }
}

class Utilities {
    constructor(lang) {
        this.lang = lang;
        this.parsePropValString = this.parsePropValString.bind(this);
    }

    /**
     * @param propType {string}
     * @param propEnum {Array}
     * @param value {string}
     * @returns {null}
     */
    parsePropValString(propType, propEnum, value) {
        let parsed = null;
        switch (propType) {
            case "bool":
                if (value === "false")
                    parsed = false;
                else if (value === "true")
                    parsed = true;
                else
                    throw this.lang.error_invalid_bool_value.format({value});
                break;
            case "int":
                parsed = parseInt(value);
                if (isNaN(parsed))
                    throw `Unable to parse integer: ${value}`;
                break;
            case "float":
                parsed = parseFloat(value);
                if (isNaN(parsed))
                    throw this.lang.error_parsing_float.format({value});
                break;
            case "str":
                parsed = value;
                break;
            default:
                throw `Unknown property type: ${propType}`;
        }
        if (propEnum && propEnum.indexOf(parsed) < 0)
            throw this.lang.error_parsing_enum.format({expected: propEnum.join(', '), value: value});
        return parsed;
    }
}

export function utilities(lang) {
    return new Utilities(lang);
}

function arrayEquals(a, b) {
    return Array.isArray(a) &&
        Array.isArray(b) &&
        a.length === b.length &&
        a.every((val, index) => val === b[index]);
}
