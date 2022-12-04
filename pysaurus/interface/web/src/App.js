import { Test } from "./pages/Test.js";
import { HomePage } from "./pages/HomePage.js";
import { VideosPage } from "./pages/VideosPage.js";
import { PropertiesPage } from "./pages/PropertiesPage.js";
import { DatabasesPage } from "./pages/DatabasesPage.js";
import { backend_error, python_call } from "./utils/backend.js";
import {
	VIDEO_DEFAULT_PAGE_NUMBER,
	VIDEO_DEFAULT_PAGE_SIZE,
} from "./utils/constants.js";
import { LangContext } from "./language.js";

export class App extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			page: null,
			parameters: {},
			lang: window.PYTHON_LANG,
			languages: [],
		};
		APP_STATE.lang = this.state.lang;
		this.loadPage = this.loadPage.bind(this);
		this.loadPropertiesPage = this.loadPropertiesPage.bind(this);
		this.loadVideosPage = this.loadVideosPage.bind(this);
		this.getLanguages = this.getLanguages.bind(this);
	}

	render() {
		return (
			<LangContext.Provider value={this.state.lang}>
				{this.renderPage()}
			</LangContext.Provider>
		);
	}

	renderPage() {
		const parameters = this.state.parameters;
		const page = this.state.page;
		if (!page) return "Opening ...";
		if (page === "test") return <Test app={this} parameters={parameters} />;
		if (page === "databases")
			return <DatabasesPage app={this} parameters={parameters} />;
		if (page === "home") return <HomePage app={this} parameters={parameters} />;
		if (page === "videos") return <VideosPage app={this} parameters={parameters} />;
		if (page === "properties")
			return <PropertiesPage app={this} parameters={parameters} />;
	}

	componentDidMount() {
		if (!this.state.page) {
			python_call("get_app_state")
				.then((appState) => this.dbHome(appState))
				.catch(backend_error);
		}
	}

	loadPage(pageName, parameters = undefined, otherState = undefined) {
		parameters = parameters ? parameters : {};
		const state = Object.assign({}, otherState || {}, {
			page: pageName,
			parameters: parameters,
		});
		this.setState(state);
	}

	// Public methods for children components.

	getLanguages() {
		return this.state.languages;
	}

	setLanguage(name) {
		python_call("set_language", name)
			.then((lang) => {
				APP_STATE.lang = lang;
				this.setState({ lang });
			})
			.catch(backend_error);
	}

	dbHome(appState = undefined) {
		this.loadPage(
			"databases",
			appState,
			appState ? { languages: appState.languages } : undefined
		);
	}

	dbUpdate(...command) {
		this.loadPage("home", { command });
	}

	loadVideosPage(pageSize = undefined, pageNumber = undefined) {
		if (pageSize === undefined) pageSize = VIDEO_DEFAULT_PAGE_SIZE;
		if (pageNumber === undefined) pageNumber = VIDEO_DEFAULT_PAGE_NUMBER;
		python_call("backend", null, pageSize, pageNumber)
			.then((info) => this.loadPage("videos", info))
			.catch(backend_error);
	}

	loadPropertiesPage() {
		python_call("describe_prop_types")
			.then((definitions) =>
				this.loadPage("properties", { definitions: definitions })
			)
			.catch(backend_error);
	}
}
