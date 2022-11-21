/** Interface language in a React context . **/
export const LangContext = React.createContext({});

/**
 * Translate text
 * @param text {string} - text to translate
 * @param placeholders {Object} - optional - map of values to use to format text
 * @returns {string} - text translated
 */
export function tr(text, placeholders = null) {
	if (placeholders !== null) text = text.format(placeholders);
	return text;
}
