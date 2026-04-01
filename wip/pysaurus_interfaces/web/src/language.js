import { formatString } from "./utils/functions.js";
import { markdownToReact } from "./utils/markdown.js";

/**
 * Translate text
 * @param text {string} - text to translate
 * @param placeholders {Object} - optional - map of values to use to format text
 * @param markdown {string} - optional - tell if text must be formatted from markdown
 * If null, no formatting
 * if "markdown", formatted from markdown with inline = false
 * if "markdown-inline", formatted from markdown with inline = true
 * @returns {string} - text translated
 */
export function tr(text, placeholders = null, markdown = null) {
	if (placeholders !== null) text = formatString(text, placeholders);
	if (markdown !== null) {
		let inline;
		if (markdown === "markdown") inline = false;
		else if (markdown === "markdown-inline") inline = true;
		else throw new Error(`Unknown markdown hint: ${markdown}, expected "markdown" or "markdown-inline"`);
		text = markdownToReact(text, inline);
	}
	return text;
}
