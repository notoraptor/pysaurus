export class Shortcut {
	/**
	 * Initialize.
	 * @param shortcut {string}
	 */
	constructor(shortcut) {
		const pieces = shortcut.split("+").map((piece) => piece.toLowerCase());
		const specialKeys = new Set(pieces.slice(0, pieces.length - 1));
		this.str = shortcut;
		this.ctrl = specialKeys.has("ctrl");
		this.alt = specialKeys.has("alt");
		this.shift = specialKeys.has("shift") || specialKeys.has("maj");
		this.key = pieces[pieces.length - 1];
	}

	/**
	 * Returns true if event corresponds to shortcut.
	 * @param event {KeyboardEvent}
	 */
	isPressed(event) {
		return (
			this.key === event.key.toLowerCase() &&
			this.ctrl === event.ctrlKey &&
			this.alt === event.altKey &&
			this.shift === event.shiftKey
		);
	}
}
