import { BaseComponent } from "../BaseComponent.js";
import { FancyBox } from "../dialogs/FancyBox.js";
import { tr } from "../language.js";
import { Fancybox } from "../utils/FancyboxManager.js";

function getSubTree(tree, entryName) {
	const steps = entryName.split("-");
	let subTree = tree;
	for (let step of steps) subTree = subTree[step];
	return subTree;
}

function collectPaths(tree, collection, prefix = "") {
	if (tree) {
		if (prefix.length) collection.push(prefix);
		for (let name of Object.keys(tree)) {
			const entryName = prefix.length ? prefix + "-" + name : name;
			collectPaths(tree[name], collection, entryName);
		}
	} else {
		collection.push(prefix);
	}
}

function addPaths(oldPaths, paths) {
	const newPaths = oldPaths.slice();
	for (let path of paths) {
		if (newPaths.indexOf(path) < 0) {
			newPaths.push(path);
		}
	}
	newPaths.sort();
	return newPaths;
}

function removePaths(oldPaths, paths) {
	let newPaths = oldPaths.slice();
	for (let path of paths) {
		const pos = newPaths.indexOf(path);
		if (pos >= 0) {
			newPaths.splice(pos, 1);
		}
	}
	return newPaths;
}

export class FormVideosSource extends BaseComponent {
	// tree
	// sources
	// onClose(sources)

	getInitialState() {
		return {
			paths: this.props.sources.map((path) => path.join("-")),
		};
	}

	render() {
		return (
			<FancyBox title="Select Videos">
				{this.renderTree(this.props.tree)}
				<p>{this.state.paths.length ? tr("Currently selected:") : tr("Currently selected: none")}</p>
				{this.state.paths.length ? (
					<ul>
						{this.state.paths.map((path, index) => (
							<li key={index}>
								<strong>{path.replace(/-/g, ".")}</strong>
							</li>
						))}
					</ul>
				) : (
					""
				)}
				<p className="submit mx-1 my-4">
					<button className="submit block" onClick={this.submit}>
						{tr("select")}
					</button>
				</p>
			</FancyBox>
		);
	}

	renderTree(tree, prefix = "") {
		return (
			<ul>
				{Object.keys(tree).map((name, index) => {
					const subTree = tree[name];
					const entryName = prefix.length ? prefix + "-" + name : name;
					const hasPath = this.hasPath(entryName);
					return (
						<li key={index}>
							{subTree ? (
								<div>
									<div>
										<strong>{name}</strong>{" "}
										<input
											type="radio"
											onChange={this.onChangeRadio}
											id={entryName + "0"}
											name={entryName}
											value={"select"}
											checked={hasPath}
										/>{" "}
										<label htmlFor={entryName + "0"}>select</label>{" "}
										<input
											type="radio"
											onChange={this.onChangeRadio}
											id={entryName + "1"}
											name={entryName}
											value={"develop"}
											checked={!hasPath}
										/>{" "}
										<label htmlFor={entryName + "1"}>{tr("develop")}</label>
									</div>
									{hasPath ? "" : this.renderTree(subTree, entryName)}
								</div>
							) : (
								<p>
									<label htmlFor={entryName + "0"}>
										<strong>{name}</strong>
									</label>{" "}
									<input
										type="checkbox"
										onChange={this.onChangeCheckBox}
										id={entryName + "0"}
										name={entryName}
										checked={hasPath}
									/>
								</p>
							)}
						</li>
					);
				})}
			</ul>
		);
	}

	hasPath(path) {
		return this.state.paths.indexOf(path) >= 0;
	}

	onChangeRadio(event) {
		const element = event.target;
		const name = element.name;
		const value = element.value;
		if (value === "select") {
			const pathsToRemove = [];
			collectPaths(getSubTree(this.props.tree, name), pathsToRemove, name);
			let paths = removePaths(this.state.paths, pathsToRemove);
			paths = addPaths(paths, [name]);
			this.setState({ paths });
		} else if (value === "develop") {
			const paths = removePaths(this.state.paths, [name]);
			this.setState({ paths });
		}
	}

	onChangeCheckBox(event) {
		const element = event.target;
		const name = element.name;
		let paths;
		if (element.checked) {
			paths = addPaths(this.state.paths, [name]);
		} else {
			paths = removePaths(this.state.paths, [name]);
		}
		this.setState({ paths });
	}

	submit() {
		Fancybox.close();
		if (this.state.paths.length) this.props.onClose(this.state.paths.map((path) => path.split("-")));
	}
}
