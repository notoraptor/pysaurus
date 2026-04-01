import { NotificationManager } from "../src/utils/NotificationManager.js";

class Test {
	constructor() {
		this.onA = 1;
		this.onB = this.onB.bind(this);
		this.onC = this.onC.bind(this);
	}
	onB(n) {
		console.log(`Calling ${this.constructor.name} for notification B: ${JSON.stringify(n)}`);
	}
	onC(n) {
		console.log(`Calling ${this.constructor.name} for notification C: ${JSON.stringify(n)}`);
	}
}

class ReTest extends Test {
	constructor() {
		super();
		this.onD = this.onD.bind(this);
		this.notify = this.notify.bind(this);
	}
	onB(n) {
		console.log(`Calling ${this.constructor.name} for notification B: ${JSON.stringify(n)}`);
	}
	onC(n) {
		console.log(`Calling ${this.constructor.name} for notification C: ${JSON.stringify(n)}`);
	}
	onD(n) {
		console.log(`Calling ${this.constructor.name} for notification D: ${JSON.stringify(n)}`);
	}
	notify(n) {
		console.log(`Generic call from ${this.constructor.name} for notification ${n.name}`);
	}
}

console.log("Hello world");
const nm = new NotificationManager();
const test = new Test();
const rt = new ReTest();
nm.installFrom(test);
nm.installFrom(rt);
nm.call({ name: "A", value: "rara" });
nm.call({ name: "B", value: "rbrb" });
nm.call({ name: "C", value: "rcrc" });
nm.call({ name: "D", value: "rdrd" });
nm.uninstallFrom(rt);
nm.call({ name: "A", value: "rara" });
nm.call({ name: "B", value: "rbrb" });
nm.call({ name: "C", value: "rcrc" });
nm.call({ name: "D", value: "rdrd" });
