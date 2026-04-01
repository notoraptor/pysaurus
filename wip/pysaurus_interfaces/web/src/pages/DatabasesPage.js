import { BaseComponent } from "../BaseComponent.js";
import { PathsInput } from "../components/PathsInput.js";
import { tr } from "../language.js";

export class DatabasesPage extends BaseComponent {
	// parameters: {databases: [name: str], languages: [name: str]}
	// app: App

	getInitialState() {
		return {
			name: "",
			paths: [],
			update: false,
		};
	}

	render() {
		const languages = this.props.parameters.language_names;
		const paths = Array.from(this.state.paths);
		paths.sort();
		return (
			<div id="databases" className="text-center">
				<h1>
					{tr("Welcome to {name}", {
						name: window.PYTHON_APP_NAME,
					})}
				</h1>
				<table className="w-100 table-layout-fixed">
					<tbody>
						{languages.length > 1 ? (
							<tr>
								<td className="text-right">
									<label htmlFor="language">{tr("Language:")}:</label>
								</td>
								<td className="text-left">
									<select
										id="language"
										value={window.PYTHON_LANGUAGE}
										onChange={this.onChangeLanguage}>
										{languages.map((language, index) => (
											<option key={index} value={language}>
												{language}
											</option>
										))}
									</select>
								</td>
							</tr>
						) : (
							""
						)}
						<tr>
							<td>
								<h2>{tr("Create a database")}</h2>
								<div className="p-1">
									<input
										type="text"
										className="w-100"
										value={this.state.name}
										onChange={this.onChangeName}
										placeholder={tr("Database name.")}
									/>
								</div>
								<h3>{tr("Database folders and files")}</h3>
								<div className="vertical new-paths">
									<PathsInput onUpdate={this.onUpdatePaths} data={this.state.paths} />
								</div>
								<div className="p-1">
									<button className="block" onClick={this.createDatabase}>
										{tr("create database")}
									</button>
								</div>
							</td>
							<td>
								<h2>
									{tr("Open a database ({count} available)", {
										count: this.props.parameters.database_names.length,
									})}
								</h2>
								<div className="p-1">
									<input
										type="checkbox"
										id="update"
										checked={this.state.update}
										onChange={this.onChangeUpdate}
									/>{" "}
									<label htmlFor="update">{tr("update after opening")}</label>
								</div>
								<h3>{tr("Click on a database to open it")}</h3>
								{this.props.parameters.database_names.map((database, index) => (
									<div className="p-1" key={index}>
										<button className="block" onClick={() => this.openDatabase(database)}>
											{database}
										</button>
									</div>
								))}
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		);
	}

	onChangeLanguage(event) {
		this.props.app.setLanguage(event.target.value);
	}

	onChangeName(event) {
		const name = event.target.value;
		if (this.state.name !== name) {
			this.setState({ name });
		}
	}

	onChangeUpdate(event) {
		this.setState({ update: event.target.checked });
	}

	createDatabase() {
		// TODO: flag `update` should be either reserved to update_database, or display as global flag into this page
		this.props.app.dbUpdate("create_database", this.state.name, Array.from(this.state.paths), this.state.update);
	}

	openDatabase(name) {
		this.props.app.dbUpdate("open_database", name, this.state.update);
	}

	onUpdatePaths(paths) {
		this.setState({ paths });
	}
}
