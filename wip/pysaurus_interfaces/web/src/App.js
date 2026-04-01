import { BaseComponent } from "./BaseComponent.js";
import { DatabasesPage } from "./pages/DatabasesPage.js";
import { HomePage } from "./pages/HomePage.js";
import { PropertiesPage } from "./pages/PropertiesPage.js";
import { Test } from "./pages/Test.js";
import { VideosPage } from "./pages/VideosPage.js";
import { Backend, backend_error, python_multiple_call } from "./utils/backend.js";
import { APP_STATE } from "./utils/globals.js";

export class App extends BaseComponent {
	constructor(props) {
		super(props);
		APP_STATE.lang = this.state.lang;
	}

	getInitialState() {
		return {
			page: null,
			parameters: {},
			lang: window.PYTHON_LANG,
			languages: [],
		};
	}

	render() {
		const parameters = this.state.parameters;
		const page = this.state.page;
		if (!page) return "Opening ...";
		if (page === "test") return <Test app={this} parameters={parameters} />;
		if (page === "databases") return <DatabasesPage app={this} parameters={parameters} />;
		if (page === "home") return <HomePage app={this} parameters={parameters} />;
		if (page === "videos") return <VideosPage app={this} parameters={parameters} />;
		if (page === "properties") return <PropertiesPage app={this} parameters={parameters} />;
	}

	componentDidMount() {
		if (!this.state.page) {
			python_multiple_call(["get_language_names"], ["get_database_names"])
				.then(([language_names, database_names]) => this.dbHome({ language_names, database_names }))
				.catch(backend_error);
		}
	}

	loadPage(pageName, parameters = undefined, otherState = undefined) {
		this.setState(
			Object.assign({}, otherState || {}, {
				page: pageName,
				parameters: parameters || {},
			}),
		);
	}

	// Public methods for children components.

	getLanguages() {
		return this.state.languages;
	}

	setLanguage(name) {
		Backend.set_language(name)
			.then((lang) => {
				APP_STATE.lang = lang;
				this.setState({ lang });
			})
			.catch(backend_error);
	}

	dbHome(appState = undefined) {
		const localState = {};
		if (appState.language_names) {
			localState.languages = appState.language_names;
		} else {
			appState.language_names = this.getLanguages();
		}
		this.loadPage("databases", appState, localState);
	}

	dbUpdate(...command) {
		this.loadPage("home", { command });
	}

	async loadVideosPage(pageSize = undefined, pageNumber = undefined) {
		try {
			const info = await Backend.backend(pageSize, pageNumber);
			this.loadPage("videos", info);
		} catch (error) {
			backend_error(error);
		}
	}

	loadPropertiesPage() {
		Backend.describe_prop_types()
			.then((definitions) => this.loadPage("properties", { definitions: definitions }))
			.catch(backend_error);
	}
}
