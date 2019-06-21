export class JavascriptDuration {
	constructor(microseconds) {
		const solidSeconds = Math.floor(microseconds / 1000000);
		const solidMinutes = Math.floor(solidSeconds / 60);
		const solidHours = Math.floor(solidMinutes / 60);
		this.days = Math.floor(solidHours / 24);
		this.hours = solidHours % 24;
		this.minutes = solidMinutes % 60;
		this.seconds = solidSeconds % 60;
		this.microseconds = microseconds % 1000000;
		this.totalMicroseconds = microseconds;
	}

	getPieces() {
		const labels = ['d', 'h', 'm', 's', 'ms'];
		const values = [this.days, this.hours, this.minutes, this.seconds, this.microseconds];
		const view = [];
		for (let i = 0; i < labels.length; ++i) {
			if (values[i])
				view.push([values[i], labels[i]]);
		}
		if (!view.length)
			view.push([0, 's']);
		return view;
	}

	toString() {
		return this.getPieces().map(piece => `${piece[0]}${piece[1]}`).join(' ');
	}
}
