import { BaseComponent } from "../BaseComponent.js";
import { Cross } from "../components/Cross.js";
import { ComponentController, SetInput } from "../components/SetInput.js";
import { Dialog } from "../dialogs/Dialog.js";
import { Fancybox } from "../utils/FancyboxManager.js";
import { PAGE_SIZES } from "../utils/constants.js";

export class Test extends BaseComponent {
	getInitialState() {
		return {
			pageSize: PAGE_SIZES[0],
			confirmDeletion: false,
			arr: ["a", "b", "ccc"],
		};
	}

	render() {
		const c = new ComponentController(this, "arr");
		return (
			<div>
				<SetInput identifier="entry" controller={c} values={["my", "name", "is", "Emninem"]} />
				Hello! <Cross action={() => console.log("cross!")} />
				<a href="https://google.fr">yayayayayaya!</a>
				<input type="text" />
				Hello! <button onClick={() => this.fancy()}>click here!</button>
			</div>
		);
	}

	fancy() {
		Fancybox.load(
			<Dialog title={"Test Fancy Box 2!"} action={() => console.log("Choice: yes!")}>
				<h1>hello world {this.state.pageSize}</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
				<h1>hello world</h1>
			</Dialog>,
		);
	}
}
